import gymnasium as gym
from gymnasium import spaces
import numpy as np
import ipaddress
from collections import deque, defaultdict

class HTTPServerEnv(gym.Env):
    def __init__(self, buffer_size=100, user_ips=None, load_threshold=0.8, hazard_index=1):
        super(HTTPServerEnv, self).__init__()
        
        # Параметры буфера и пользовательских адресов
        self.buffer_size = buffer_size  # Размер буфера запросов
        if user_ips:
            self.user_ips = set(user_ips)  # Множество пользовательских IP-адресов
        else:
            self.user_ips = set(self.generate_random_ips(250))  # Генерация 250 случайных пользовательских адресов
        
        # Параметры загрузки и индекса опасности
        self.load_threshold = load_threshold  # Порог загрузки
        self.hazard_index = hazard_index  # Индекс опасности
        
        # Определение пространства состояний
        self.observation_space = spaces.Box(
            low=np.array([0, 0, 0, 0, 0, 0, 0, 0], dtype=np.float32),  # Нижняя граница
            high=np.array([1000000, 1000000, 1000, 1000, 10000, 1, 1, 256**4], dtype=np.float32),  # Верхняя граница
            dtype=np.float32
        )
        
        # Определение пространства действий
        self.action_space = spaces.Discrete(4)  # 0 - принять, 1 - отклонить, 2 - блокировать источник, 3 - блокировать группу
        
        # Инициализация состояния
        self.state = np.zeros(8, dtype=np.float32)
        
        # Параметры симуляции
        self.max_messages = 1000
        self.current_message_count = 0
        self.blocked_ips = set()  # Множество заблокированных IP-адресов
        self.blocked_groups = set()  # Множество заблокированных групп
        
        # Статистика по источникам
        self.source_stats = defaultdict(lambda: {
            "last_time": 0,
            "intervals": [],
            "total_messages": 0,
        })
        
        # Размер трафика по группам
        self.group_traffic = defaultdict(int)
        
        # Буфер запросов
        self.request_buffer = deque(maxlen=self.buffer_size)
        self.fill_buffer()  # Заполнение буфера начальными запросами

    def reset(self):
        # Сброс среды в начальное состояние
        self.state = np.zeros(8, dtype=np.float32)
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
        self.fill_buffer()  # Заполнение буфера начальными запросами
        return self.state

    def step(self, action):
        # Симуляция обработки запроса
        done = False
        info = {}
        
        # Получение текущего запроса из буфера
        if len(self.request_buffer) == 0:
            self.fill_buffer()  # Если буфер пуст, заполняем его
        source_ip, is_user_request = self.request_buffer[0]  # Берем первый элемент без удаления
        
        # Обновление состояния
        message_size = np.random.randint(100, 1000000)
        self.state[0] = message_size  # Размер сообщения
        self.state[7] = int(source_ip.split('.')[-1])  # Последний октет IPv4-адреса (для простоты)
        
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
        self.state[2] = avg_time  # Среднее время между сообщениями
        self.state[3] = avg_abs_deviation  # Среднее абсолютное отклонение
        self.state[4] = source_stat["total_messages"]  # Число сообщений
        
        # Обновление размера трафика по группе
        group = self.get_source_group(source_ip)
        self.group_traffic[group] += message_size
        self.state[1] = self.group_traffic[group]  # Размер трафика
        
        # Случайная загрузка CPU и памяти
        self.state[5] = np.random.uniform(0, 1)  # CPU load
        self.state[6] = np.random.uniform(0, 1)  # Memory load
        
        # Подсчет награды
        reward = self.get_reward(action, is_user_request, group)
        
        # Проверка условия завершения
        self.current_message_count += 1
        if self.current_message_count >= self.max_messages:
            done = True
        
        return self.state, reward, done, info


    def get_reward(self, action, is_user_request, group):
        # Подсчет награды в зависимости от действия
        max_load = max(self.state[5], self.state[6])  # Максимум загрузки CPU и памяти
        
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
        for ip, is_user_request in self.request_buffer:
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


    def fill_buffer(self):
        # Заполнение буфера случайными запросами
        while len(self.request_buffer) < self.buffer_size:
            source_ip = self.generate_random_ip()
            is_user_request = source_ip in self.user_ips
            self.request_buffer.append((source_ip, is_user_request))


    def render(self, mode='human'):
        pass