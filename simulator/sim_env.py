import gymnasium as gym
from gymnasium import spaces
import numpy as np
import ipaddress
from collections import deque, defaultdict

class HTTPServerEnv(gym.Env):
    def __init__(self, buffer_size=100, user_ips=None, load_threshold=0.8, hazard_index=1, user_message_sizes=None, user_request_prob=0.2):
        super(HTTPServerEnv, self).__init__()
        
        # Параметры буфера и пользовательских адресов
        self.buffer_size = buffer_size
        self.user_ips = set(user_ips) if user_ips else set(self.generate_random_ips(250))
        
        # Параметры загрузки и индекса опасности
        self.load_threshold = load_threshold
        self.hazard_index = hazard_index
        
        # Пул фиксированных размеров сообщений для пользовательских адресов
        self.user_message_sizes = user_message_sizes if user_message_sizes else [100, 200, 300, 400, 500]
        
        # Вероятность добавления пользовательского запроса
        self.user_request_prob = user_request_prob
        
        # Определение пространства состояний (7 элементов)
        self.observation_space = spaces.Box(
            low=np.array([0, 0, 0, 0, 0, 0, 0], dtype=np.float32),
            high=np.array([1000000, 1000000, 1000, 1000, 10000, 1, 1], dtype=np.float32),
            dtype=np.float32
        )
        
        # Определение пространства действий
        self.action_space = spaces.Discrete(4)  # 0 - принять, 1 - отклонить, 2 - блокировать источник, 3 - блокировать группу
        
        # Параметры симуляции
        self.max_messages = 700
        self.current_message_count = 0
        self.blocked_ips = set()
        self.blocked_groups = set()
        
        # Статистика по источникам
        self.source_stats = defaultdict(lambda: {
            "last_time": 0,
            "intervals": [],
            "total_messages": 0,
        })
        
        # Размер трафика по группам
        self.group_traffic = defaultdict(int)
        
        # Буфер запросов (хранит state, source_ip, is_user_request)
        self.request_buffer = deque(maxlen=self.buffer_size)

    def reset(self):
        # Сброс среды в начальное состояние
        self.current_message_count = 0
        self.blocked_ips = set()
        self.blocked_groups = set()
        self.source_stats = defaultdict(lambda: {
            "last_time": 0,
            "intervals": [],
            "total_messages": 0,
        })
        self.group_traffic = defaultdict(int)
        self.request_buffer.clear()
        self.fill_buffer()  # Первичное заполнение буфера
        return self.request_buffer[0][0]

    def step(self, action):
        # Симуляция обработки запроса
        done = False
        info = {}
        
        # Получение текущего запроса из буфера с удалением
        state, source_ip, is_user_request = self.request_buffer.popleft()
        
        # Обновление статистики по источнику
        current_time = self.current_message_count
        source_stat = self.source_stats[source_ip]
        if source_stat["last_time"] > 0:
            interval = current_time - source_stat["last_time"]
            source_stat["intervals"].append(interval)
        source_stat["last_time"] = current_time
        source_stat["total_messages"] += 1
        
        # Расчет среднего времени и отклонения
        if len(source_stat["intervals"]) > 0:
            avg_time = np.mean(source_stat["intervals"])
            avg_abs_deviation = np.mean(np.abs(np.array(source_stat["intervals"]) - avg_time))
        else:
            avg_time = 0
            avg_abs_deviation = 0
        
        # Обновление размера трафика по группе
        group = self.get_source_group(source_ip)
        if is_user_request:
            message_size = np.random.choice(self.user_message_sizes)
        else:
            message_size = np.random.randint(100, 1000000)
        self.group_traffic[group] += message_size
        
        # Случайная загрузка CPU и памяти
        cpu_load = np.random.uniform(0, 1)
        memory_load = np.random.uniform(0, 1)
        
        # Создание нового состояния с использованием generate_random_state
        new_state, _, _ = self.generate_random_state()
        
        # Подсчет награды
        reward = self.get_reward(action, is_user_request, source_ip, group, cpu_load, memory_load)
        
        # Обработка действий: блокировка IP-адреса или группы
        if action == 2:  # Блокировать источник
            self.blocked_ips.add(source_ip)
        elif action == 3:  # Блокировать группу
            self.blocked_groups.add(group)
        
        # Удаление заблокированных запросов из буфера
        self.remove_blocked_requests()
        
        # Добавление нового запроса в буфер
        self.add_request_to_buffer(new_state)
        
        # Дополняем буфер до 100 элементов, если он опустел после удаления заблокированных запросов
        while len(self.request_buffer) < self.buffer_size:
            self.add_request_to_buffer(self.generate_random_state()[0])
        
        # Проверка условия завершения
        self.current_message_count += 1
        if self.current_message_count >= self.max_messages:
            done = True
        
        # Возвращаем новое состояние (нулевой элемент буфера без удаления)
        next_state = self.request_buffer[0][0]
        return next_state, reward, done, info

    def get_reward(self, action, is_user_request, source_ip, group, cpu_load, memory_load):
        # Подсчет награды в зависимости от действия
        max_load = max(cpu_load, memory_load)
        
        if max_load > self.load_threshold:
            if action in [2, 3]:  # Блокировка источника или группы
                tp, fp = self.count_requests_in_buffer(group)
                return (max_load / self.load_threshold * self.hazard_index) * tp - (2 / (max_load / self.load_threshold * self.hazard_index) * fp)
            else:  # Действие влияет на 1 запрос
                if is_user_request and action == 0:  # Приняли пользователя
                    return 0
                elif is_user_request and action in [1, 2]:  # Отклонили или заблокировали пользователя
                    return -2 / (max_load / self.load_threshold * self.hazard_index)
                elif not is_user_request and action == 0:  # Приняли атакующего
                    return -(max_load / self.load_threshold * self.hazard_index)
                elif not is_user_request and action in [1, 2]:  # Отклонили или заблокировали атакующего
                    return max_load / self.load_threshold * self.hazard_index
        else:
            if action in [2, 3]:  # Блокировка источника или группы
                tp, fp = self.count_requests_in_buffer(group)
                return tp - 2 * fp
            else:  # Действие влияет на 1 запрос
                if is_user_request and action == 0:  # Приняли пользователя
                    return 0
                elif is_user_request and action in [1, 2]:  # Отклонили или заблокировали пользователя
                    return -2
                elif not is_user_request and action == 0:  # Приняли атакующего
                    return -1
                elif not is_user_request and action in [1, 2]:  # Отклонили или заблокировали атакующего
                    return 1

    def count_requests_in_buffer(self, group):
        # Подсчет числа запросов от пользователей и атакующих в буфере
        tp = 0  # True Positives (запросы от пользователей)
        fp = 0  # False Positives (запросы от атакующих)
        for state, ip, is_user_request in self.request_buffer:
            if self.get_source_group(ip) == group:
                if is_user_request:
                    tp += 1
                else:
                    fp += 1
        return tp, fp

    def generate_random_ip(self):
        # Генерация случайного IPv4-адреса, исключая специальные адреса
        while True:
            ip = str(ipaddress.IPv4Address(np.random.randint(0, 256**4)))
            if ip not in ["127.0.0.1", "0.0.0.0"]:
                return ip

    def generate_random_ips(self, count):
        # Генерация списка случайных IPv4-адресов
        ips = set()
        while len(ips) < count:
            ips.add(self.generate_random_ip())
        return list(ips)

    def get_source_group(self, source_ip):
        # Группировка по подсети /24
        ip = ipaddress.IPv4Address(source_ip)
        return str(ipaddress.IPv4Network(f"{ip}/24", strict=False).network_address)

    def generate_random_state(self):
        # Определяем, является ли запрос пользовательским
        is_user_request = np.random.rand() < self.user_request_prob
        
        # Генерация IP-адреса в зависимости от типа запроса
        if is_user_request:
            source_ip = np.random.choice(list(self.user_ips))
        else:
            while True:
                source_ip = self.generate_random_ip()
                if source_ip not in self.user_ips:
                    break
        
        # Генерация размера сообщения
        if is_user_request:
            message_size = np.random.choice(self.user_message_sizes)
        else:
            message_size = np.random.randint(100, 1000000)
        
        # Группировка по подсети /24
        group = self.get_source_group(source_ip)
        
        # Обновление размера трафика по группе
        self.group_traffic[group] += message_size
        
        # Случайная загрузка CPU и памяти
        cpu_load = np.random.uniform(0, 1)
        memory_load = np.random.uniform(0, 1)
        
        # Генерация статистики по источнику
        source_stat = self.source_stats[source_ip]
        if source_stat["last_time"] > 0:
            avg_time = np.mean(source_stat["intervals"]) if source_stat["intervals"] else 0
            avg_abs_deviation = np.mean(np.abs(np.array(source_stat["intervals"]) - avg_time)) if source_stat["intervals"] else 0
        else:
            avg_time = 0
            avg_abs_deviation = 0
        
        # Создание заполненного состояния
        state = np.array([
            message_size,
            self.group_traffic[group],
            avg_time,
            avg_abs_deviation,
            source_stat["total_messages"],
            cpu_load,
            memory_load,
        ], dtype=np.float32)
        
        return state, source_ip, is_user_request

    def fill_buffer(self):
        # Дополняем буфер до 100 элементов
        while len(self.request_buffer) < self.buffer_size:
            state, source_ip, is_user_request = self.generate_random_state()
            self.request_buffer.append((state, source_ip, is_user_request))

    def add_request_to_buffer(self, state):
        # Определяем класс запроса: пользовательский или атакующий
        is_user_request = np.random.rand() < self.user_request_prob
        
        # Генерация IP-адреса в зависимости от класса запроса
        while True:
            if is_user_request:
                source_ip = np.random.choice(list(self.user_ips))
            else:
                source_ip = self.generate_random_ip()
                if source_ip not in self.user_ips:
                    break
            
            # Проверяем, что IP-адрес и его группа не заблокированы
            if source_ip not in self.blocked_ips and self.get_source_group(source_ip) not in self.blocked_groups:
                break
        
        # Добавление запроса в буфер
        self.request_buffer.append((state, source_ip, is_user_request))

    def remove_blocked_requests(self):
        # Удаляем запросы, которые принадлежат заблокированным IP-адресам или группам
        self.request_buffer = deque(
            (state, ip, is_user) for state, ip, is_user in self.request_buffer
            if ip not in self.blocked_ips and self.get_source_group(ip) not in self.blocked_groups
        )

    def render(self, mode='human'):
        pass