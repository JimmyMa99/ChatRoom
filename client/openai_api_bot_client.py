import socket
import threading
import json
from cmd import Cmd
from openai import OpenAI

_api_key='sk-1'
_base_url=''

class Client(Cmd):
    """
    客户端
    """
    prompt = ''
    intro = '[Welcome] 简易聊天室客户端(Cli版)\n' + '[Welcome] 输入help来获取帮助\n'

    def __init__(self):
        """
        构造
        """
        super().__init__()
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__id = None
        self.__nickname = None
        self.__isLogin = False
        self.use_bot = False
        self.bot_history = []
        self.bot_prompt = 'bot> '

    def __receive_message_thread(self):
        """
        接受消息线程
        """
        while self.__isLogin:
            # noinspection PyBroadException
            try:
                buffer = self.__socket.recv(1024).decode()
                obj = json.loads(buffer)
                message = '[' + str(obj['sender_nickname']) + '(' + str(obj['sender_id']) + ')' + ']'+str(obj['message'])
                print('[' + str(obj['sender_nickname']) + '(' + str(obj['sender_id']) + ')' + ']', obj['message'])
                if self.use_bot:
                    response = self.get_response(message, self.bot_history)
                    print(self.bot_prompt + response)
                    self.bot_history.append(message)
                    self.bot_history.append(response)
                    self.do_send(response)
            except Exception as e:
                print('[Client] 无法从服务器获取数据')
                print(e)

    def __send_message_thread(self, message):
        """
        发送消息线程
        :param message: 消息内容
        """
        self.__socket.send(json.dumps({
            'type': 'broadcast',
            'sender_id': self.__id,
            'message': message
        }).encode())

    def start(self):
        """
        启动客户端
        """
        self.__socket.connect(('127.0.0.1', 8888))
        self.cmdloop()

    def get_response(self,prompt, history):
                client = OpenAI(
                            api_key=_api_key,
                            # base_url='https://api.moonshot.cn/v1',
                            base_url=_base_url,
                        )

                messages = [{
                    'role':
                    'system',
                    'content':''
                }]

                messages.append({'role': 'user', 'content': prompt})


                completion = client.chat.completions.create(
                    model='gpt-3.5-turbo',
                    messages=messages,
                    temperature=0.3,
                )
                return completion.choices[0].message.content

    def do_login(self, args):
        """
        登录聊天室
        :param args: 参数
        """
        nickname = args.split(' ')[0]

        # 将昵称发送给服务器，获取用户id
        self.__socket.send(json.dumps({
            'type': 'login',
            'nickname': nickname
        }).encode())
        # 尝试接受数据
        # noinspection PyBroadException
        try:
            buffer = self.__socket.recv(1024).decode()
            obj = json.loads(buffer)
            if obj['id']:
                self.__nickname = nickname
                self.__id = obj['id']
                self.__isLogin = True
                print('[Client] 成功登录到聊天室')

                # 开启子线程用于接受数据
                thread = threading.Thread(target=self.__receive_message_thread)
                thread.setDaemon(True)
                thread.start()
            else:
                print('[Client] 无法登录到聊天室')
        except Exception:
            print('[Client] 无法从服务器获取数据')

    def do_send(self, args):
        """
        发送消息
        :param args: 参数
        """
        message = args
        # 显示自己发送的消息
        print('[' + str(self.__nickname) + '(' + str(self.__id) + ')' + ']', message)
        # 开启子线程用于发送数据
        thread = threading.Thread(target=self.__send_message_thread, args=(message,))
        thread.setDaemon(True)
        thread.start()

    def do_setbot(self, args=None):
        """
        设置基于openai的聊天机器人
        """
        self.use_bot = True
        self.__socket.send(json.dumps({
            'type': 'login',
            'nickname': 'bot'
        }).encode())
        try:
            buffer = self.__socket.recv(1024).decode()
            obj = json.loads(buffer)
            if obj['id']:
                self.__nickname = 'bot'
                self.__id = obj['id']
                self.__isLogin = True
                print('[Bot] 成功登录到聊天室')

                # 开启子线程用于接受数据
                thread = threading.Thread(target=self.__receive_message_thread)
                thread.setDaemon(True)
                thread.start()
            else:
                print('[Bot] 无法登录到聊天室')
        except Exception:
            print('[Bot] 无法从服务器获取数据')

    def do_logout(self, args=None):
        """
        登出
        :param args: 参数
        """
        self.__socket.send(json.dumps({
            'type': 'logout',
            'sender_id': self.__id
        }).encode())
        self.__isLogin = False
        return True

    def do_help(self, arg):
        """
        帮助
        :param arg: 参数
        """
        command = arg.split(' ')[0]
        if command == '':
            print('[Help] login nickname - 登录到聊天室，nickname是你选择的昵称')
            print('[Help] send message - 发送消息，message是你输入的消息')
            print('[Help] logout - 退出聊天室')
        elif command == 'login':
            print('[Help] login nickname - 登录到聊天室，nickname是你选择的昵称')
        elif command == 'send':
            print('[Help] send message - 发送消息，message是你输入的消息')
        elif command == 'logout':
            print('[Help] logout - 退出聊天室')
        else:
            print('[Help] 没有查询到你想要了解的指令')
