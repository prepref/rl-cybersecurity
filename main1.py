from utils import message_generator

def main():
    message_generator.start(is_user=True, min_intv=1, max_intv=2, nums_messages=50)
    message_generator.start(is_user=False, min_intv=1, max_intv=1, nums_messages=150)
    message_generator.start(is_user=True, min_intv=4, max_intv=7, nums_messages=150)
    message_generator.start(is_user=False, min_intv=1, max_intv=1, nums_messages=300)
    message_generator.start(is_user=True, min_intv=2, max_intv=4, nums_messages=300)
    message_generator.start(is_user=False, min_intv=1, max_intv=1, nums_messages=300)
    message_generator.start(is_user=True, min_intv=2, max_intv=4, nums_messages=300)
    message_generator.start(is_user=False, min_intv=1, max_intv=1, nums_messages=300)
    message_generator.start(is_user=True, min_intv=2, max_intv=4, nums_messages=300)
    message_generator.start(is_user=False, min_intv=1, max_intv=1, nums_messages=300)
    message_generator.start(is_user=True, min_intv=2, max_intv=4, nums_messages=300)
    message_generator.start(is_user=False, min_intv=1, max_intv=1, nums_messages=300)
    message_generator.start(is_user=True, min_intv=2, max_intv=4, nums_messages=300)
    message_generator.start(is_user=False, min_intv=1, max_intv=1, nums_messages=300)
    message_generator.start(is_user=True, min_intv=2, max_intv=4, nums_messages=300)

if __name__ == '__main__':
    main()