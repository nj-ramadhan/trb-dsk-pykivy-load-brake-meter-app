from kivy.clock import Clock
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.resources import resource_add_path
from kivy.uix.screenmanager import ScreenManager
from kivymd.font_definitions import theme_font_styles
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.toast import toast
from kivymd.app import MDApp
import os, sys, time, numpy as np
import configparser, hashlib, mysql.connector
from pymodbus.client import ModbusTcpClient

colors = {
    "Red"   : {"A200": "#FF2A2A","A500": "#FF8080","A700": "#FFD5D5",},
    "Gray"  : {"200": "#CCCCCC","500": "#ECECEC","700": "#F9F9F9",},
    "Blue"  : {"200": "#4471C4","500": "#5885D8","700": "#6C99EC",},
    "Green" : {"200": "#2CA02C","500": "#2DB97F", "700": "#D5FFD5",},
    "Yellow": {"200": "#ffD42A","500": "#ffE680","700": "#fff6D5",},

    "Light" : {"StatusBar": "E0E0E0","AppBar": "#202020","Background": "#EEEEEE","CardsDialogs": "#FFFFFF","FlatButtonDown": "#CCCCCC",},
    "Dark"  : {"StatusBar": "101010","AppBar": "#E0E0E0","Background": "#111111","CardsDialogs": "#222222","FlatButtonDown": "#DDDDDD",},
}

if getattr(sys, 'frozen', False):
    app_path = os.path.dirname(os.path.abspath(__file__))
else:
    app_path = os.path.dirname(os.path.abspath(__file__))

config_path = os.path.join(app_path, 'config.ini')
print(f"Path config.ini: {config_path}")

config = configparser.ConfigParser()
config.read(config_path)
DB_HOST = config['mysql']['DB_HOST']
DB_USER = config['mysql']['DB_USER']
DB_PASSWORD = config['mysql']['DB_PASSWORD']
DB_NAME = config['mysql']['DB_NAME']
TB_DATA = config['mysql']['TB_DATA']
TB_USER = config['mysql']['TB_USER']

MODBUS_CLIENT = ModbusTcpClient(config['modbus']['MODBUS_CLIENT'])

STANDARD_MAX_AXLE_LOAD = float(config['standard']['STANDARD_MAX_AXLE_LOAD']) # in kg
STANDARD_MAX_BRAKE = float(config['standard']['STANDARD_MAX_BRAKE']) # in kg

COUNT_STARTING = 3
COUNT_ACQUISITION = 4
TIME_OUT = 500

dt_load_l_value = 0
dt_load_r_value = 0
dt_load_flag = 0
dt_load_user = 1
dt_load_post = str(time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()))
dt_brake_value = 0
dt_brake_flag = 0
dt_brake_user = 1
dt_brake_post = str(time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()))

dt_user = ""
dt_no_antrian = ""
dt_no_reg = ""
dt_no_uji = ""
dt_nama = ""
dt_jenis_kendaraan = ""

class ScreenLogin(MDScreen):
    def __init__(self, **kwargs):
        super(ScreenLogin, self).__init__(**kwargs)

    def exec_cancel(self):
        try:
            self.ids.tx_username.text = ""
            self.ids.tx_password.text = ""    

        except Exception as e:
            toast_msg = f'Error Cancel Login: {e}'
            toast(toast_msg)

    def exec_login(self):
        global mydb, db_users
        global dt_load_user, dt_user

        try:
            input_username = self.ids.tx_username.text
            input_password = self.ids.tx_password.text   
            hashed_password = hashlib.md5(input_password.encode())

            mycursor = mydb.cursor()
            mycursor.execute(f"SELECT id_user, nama, username, password, nama FROM {TB_USER} WHERE username = '"+str(input_username)+"' and password = '"+str(hashed_password.hexdigest())+"'")
            myresult = mycursor.fetchone()
            db_users = np.array(myresult).T
            if myresult == 0:
                toast('Gagal Masuk, Nama Pengguna atau Password Salah')
            else:
                toast_msg = f'Berhasil Masuk, Selamat Datang {myresult[1]}'
                toast(toast_msg)
                dt_load_user = myresult[0]
                dt_user = myresult[1]
                self.ids.tx_username.text = ""
                self.ids.tx_password.text = "" 
                self.screen_manager.current = 'screen_main'

        except Exception as e:
            toast_msg = f'Error Login: {e}'
            toast(toast_msg)        
            toast('Gagal Masuk, Nama Pengguna atau Password Salah')

class ScreenMain(MDScreen):   
    def __init__(self, **kwargs):
        super(ScreenMain, self).__init__(**kwargs)
        global mydb, db_antrian
        global flag_conn_stat, flag_play
        global count_starting, count_get_data

        Clock.schedule_interval(self.regular_update_connection, 5)
        Clock.schedule_once(self.delayed_init, 1)

        flag_conn_stat = False
        flag_play = False

        count_starting = COUNT_STARTING
        count_get_data = COUNT_ACQUISITION

        try:
            mydb = mysql.connector.connect(host = DB_HOST,user = DB_USER,password = DB_PASSWORD,database = DB_NAME)

        except Exception as e:
            toast_msg = f'Error Initiate Database: {e}'
            toast(toast_msg)     

    def delayed_init(self, dt):
        Clock.schedule_interval(self.regular_update_display, 1)
        self.exec_reload_table()

    def on_row_press(self, instance):
        global dt_no_antrian, dt_no_reg, dt_no_uji, dt_nama, dt_jenis_kendaraan
        global dt_load_flag, dt_load_l_value, dt_load_r_value, dt_load_user, dt_load_post
        global dt_brake_flag, dt_brake_value, dt_brake_user, dt_brake_post        
        global db_antrian

        try:
            row = int(str(instance.id).replace("card",""))
            dt_no_antrian           = f"{db_antrian[0, row]}"
            dt_no_reg               = f"{db_antrian[1, row]}"
            dt_no_uji               = f"{db_antrian[2, row]}"
            dt_nama                 = f"{db_antrian[3, row]}"
            dt_jenis_kendaraan      = f"{db_antrian[4, row]}"
            dt_load_flag            = 'Belum Tes' if (int(db_antrian[5, row]) == 0) else 'Lulus' if (int(db_antrian[5, row]) == 1) else 'Gagal'
            dt_brake_flag           = 'Belum Tes' if (int(db_antrian[6, row]) == 0) else 'Lulus' if (int(db_antrian[6, row]) == 1) else 'Gagal'

        except Exception as e:
            toast_msg = f'Error Update Table: {e}'
            toast(toast_msg)   

    def regular_update_display(self, dt):
        global flag_conn_stat
        global count_starting, count_get_data
        global dt_user, dt_no_antrian, dt_no_reg, dt_no_uji, dt_nama, dt_jenis_kendaraan
        global dt_load_flag, dt_load_l_value, dt_load_r_value, dt_load_user, dt_load_post
        global dt_brake_flag, dt_brake_value, dt_brake_user, dt_brake_post
        
        try:
            screen_login = self.screen_manager.get_screen('screen_login')
            screen_load = self.screen_manager.get_screen('screen_load')
            screen_brake = self.screen_manager.get_screen('screen_brake')
            
            self.ids.lb_time.text = str(time.strftime("%H:%M:%S", time.localtime()))
            self.ids.lb_date.text = str(time.strftime("%d/%m/%Y", time.localtime()))
            screen_login.ids.lb_time.text = str(time.strftime("%H:%M:%S", time.localtime()))
            screen_login.ids.lb_date.text = str(time.strftime("%d/%m/%Y", time.localtime()))
            screen_load.ids.lb_time.text = str(time.strftime("%H:%M:%S", time.localtime()))
            screen_load.ids.lb_date.text = str(time.strftime("%d/%m/%Y", time.localtime()))
            screen_brake.ids.lb_time.text = str(time.strftime("%H:%M:%S", time.localtime()))
            screen_brake.ids.lb_date.text = str(time.strftime("%d/%m/%Y", time.localtime()))

            self.ids.lb_no_antrian.text = str(dt_no_antrian)
            self.ids.lb_no_reg.text = str(dt_no_reg)
            self.ids.lb_no_uji.text = str(dt_no_uji)
            self.ids.lb_nama.text = str(dt_nama)
            self.ids.lb_jenis_kendaraan.text = str(dt_jenis_kendaraan)

            screen_load.ids.lb_no_antrian.text = str(dt_no_antrian)
            screen_load.ids.lb_no_reg.text = str(dt_no_reg)
            screen_load.ids.lb_no_uji.text = str(dt_no_uji)
            screen_load.ids.lb_nama.text = str(dt_nama)
            screen_load.ids.lb_jenis_kendaraan.text = str(dt_jenis_kendaraan)

            screen_brake.ids.lb_no_antrian.text = str(dt_no_antrian)
            screen_brake.ids.lb_no_reg.text = str(dt_no_reg)
            screen_brake.ids.lb_no_uji.text = str(dt_no_uji)
            screen_brake.ids.lb_nama.text = str(dt_nama)
            screen_brake.ids.lb_jenis_kendaraan.text = str(dt_jenis_kendaraan)

            screen_load.ids.lb_load_l_val.text = str(dt_load_l_value)
            screen_load.ids.lb_load_r_val.text = str(dt_load_r_value)
            screen_brake.ids.lb_brake_l_val.text = str(dt_brake_value)
            screen_brake.ids.lb_brake_r_val.text = str(dt_brake_value)

            if(dt_load_flag == "Belum Tes"):
                self.ids.bt_start_load.disabled = False
            else:
                self.ids.bt_start_load.disabled = True

            if(dt_brake_flag == "Belum Tes"):
                self.ids.bt_start_brake.disabled = False
            else:
                self.ids.bt_start_brake.disabled = True

            if(not flag_play):
                screen_load.ids.bt_save.md_bg_color = colors['Green']['200']
                screen_load.ids.bt_save.disabled = False
                screen_load.ids.bt_reload.md_bg_color = colors['Red']['A200']
                screen_load.ids.bt_reload.disabled = False

                screen_brake.ids.bt_save.md_bg_color = colors['Green']['200']
                screen_brake.ids.bt_save.disabled = False
                screen_brake.ids.bt_reload.md_bg_color = colors['Red']['A200']
                screen_brake.ids.bt_reload.disabled = False

            else:
                screen_load.ids.bt_reload.disabled = True
                screen_load.ids.bt_save.disabled = True

                screen_brake.ids.bt_reload.disabled = True
                screen_brake.ids.bt_save.disabled = True

            if(not flag_conn_stat):
                self.ids.lb_comm.color = colors['Red']['A200']
                self.ids.lb_comm.text = 'PLC Tidak Terhubung'
                screen_login.ids.lb_comm.color = colors['Red']['A200']
                screen_login.ids.lb_comm.text = 'PLC Tidak Terhubung'
                screen_load.ids.lb_comm.color = colors['Red']['A200']
                screen_load.ids.lb_comm.text = 'PLC Tidak Terhubung'
                screen_brake.ids.lb_comm.color = colors['Red']['A200']
                screen_brake.ids.lb_comm.text = 'PLC Tidak Terhubung'

            else:
                self.ids.lb_comm.color = colors['Blue']['200']
                self.ids.lb_comm.text = 'PLC Terhubung'
                screen_login.ids.lb_comm.color = colors['Blue']['200']
                screen_login.ids.lb_comm.text = 'PLC Terhubung'
                screen_load.ids.lb_comm.color = colors['Blue']['200']
                screen_load.ids.lb_comm.text = 'PLC Terhubung'
                screen_brake.ids.lb_comm.color = colors['Blue']['200']
                screen_brake.ids.lb_comm.text = 'PLC Terhubung'

            if(count_starting <= 0):
                screen_load.ids.lb_test_subtitle.text = "HASIL PENGUKURAN"
                screen_load.ids.lb_load_l_val.text = str(np.round(dt_load_l_value, 2))
                screen_load.ids.lb_load_r_val.text = str(np.round(dt_load_r_value, 2))
                screen_brake.ids.lb_test_subtitle.text = "HASIL PENGUKURAN"
                screen_brake.ids.lb_brake_l_val.text = str(np.round(dt_brake_value, 2))
                screen_brake.ids.lb_brake_r_val.text = str(np.round(dt_brake_value, 2))

                if(dt_load_l_value <= STANDARD_MAX_AXLE_LOAD):
                    screen_load.ids.lb_info.text = f"Ambang Batas Beban yang diperbolehkan adalah {STANDARD_MAX_AXLE_LOAD} kg.\nBerat Roda Kendaraan Anda Dalam Range Ambang Batas"
                else:
                    screen_load.ids.lb_info.text = f"Ambang Batas Beban yang diperbolehkan adalah {STANDARD_MAX_AXLE_LOAD} kg.\nBerat Roda Kendaraan Anda Diluar Ambang Batas"

                if(dt_brake_value <= STANDARD_MAX_BRAKE):
                    screen_brake.ids.lb_info.text = f"Ambang Batas Beban yang diperbolehkan adalah {STANDARD_MAX_AXLE_LOAD} kg.\nKekuatan Pengereman Kendaraan Anda Dalam Range Ambang Batas"
                else:
                    screen_brake.ids.lb_info.text = f"Ambang Batas Beban yang diperbolehkan adalah {STANDARD_MAX_AXLE_LOAD} kg.\nKekuatan Pengereman Kendaraan Anda Diluar Ambang Batas"                

            elif(count_starting > 0):
                if(flag_play):
                    screen_load.ids.lb_test_subtitle.text = "MEMULAI PENGUKURAN"
                    screen_load.ids.lb_load_l_val.text = str(count_starting)
                    screen_load.ids.lb_load_r_val.text = " "
                    screen_load.ids.lb_info.text = "Silahkan Tempatkan Kendaraan Anda Pada Tempat yang Sudah Disediakan"

                    screen_brake.ids.lb_test_subtitle.text = "MEMULAI PENGUKURAN"
                    screen_brake.ids.lb_brake_l_val.text = str(count_starting)
                    screen_brake.ids.lb_brake_r_val.text = " "
                    screen_brake.ids.lb_info.text = "Silahkan Tempatkan Kendaraan Anda Pada Tempat yang Sudah Disediakan"

            if(count_get_data <= 0):
                if(not flag_play):
                    screen_load.ids.lb_test_result.size_hint_y = 0.25
                    screen_brake.ids.lb_test_result.size_hint_y = 0.25
                    if(dt_load_l_value <= STANDARD_MAX_AXLE_LOAD):
                        screen_load.ids.lb_test_result.md_bg_color = colors['Green']['200']
                        screen_load.ids.lb_test_result.text = "LULUS"
                        dt_load_flag = "Lulus"
                        screen_load.ids.lb_test_result.text_color = colors['Green']['700']
                    else:
                        screen_load.ids.lb_test_result.md_bg_color = colors['Red']['A200']
                        screen_load.ids.lb_test_result.text = "TIDAK LULUS"
                        dt_load_flag = "Tidak Lulus"
                        screen_load.ids.lb_test_result.text_color = colors['Red']['A700']

                    if(dt_brake_value <= STANDARD_MAX_AXLE_LOAD):
                        screen_brake.ids.lb_test_result.md_bg_color = colors['Green']['200']
                        screen_brake.ids.lb_test_result.text = "LULUS"
                        dt_brake_flag = "Lulus"
                        screen_brake.ids.lb_test_result.text_color = colors['Green']['700']
                    else:
                        screen_brake.ids.lb_test_result.md_bg_color = colors['Red']['A200']
                        screen_brake.ids.lb_test_result.text = "TIDAK LULUS"
                        dt_brake_flag = "Tidak Lulus"
                        screen_brake.ids.lb_test_result.text_color = colors['Red']['A700']

            elif(count_get_data > 0):
                screen_load.ids.lb_test_result.md_bg_color = "#EEEEEE"
                screen_load.ids.lb_test_result.text = ""

                screen_brake.ids.lb_test_result.md_bg_color = "#EEEEEE"
                screen_brake.ids.lb_test_result.text = ""

            self.ids.lb_operator.text = f'Nama Pengguna: {dt_user}' if dt_user != '' else 'Silahkan Login'
            screen_login.ids.lb_operator.text = f'Nama Pengguna: {dt_user}' if dt_user != '' else 'Silahkan Login'
            screen_load.ids.lb_operator.text = f'Nama Pengguna: {dt_user}' if dt_user != '' else 'Silahkan Login'
            screen_brake.ids.lb_operator.text = f'Nama Pengguna: {dt_user}' if dt_user != '' else 'Silahkan Login'

        except Exception as e:
            toast_msg = f'Error Update Display: {e}'
            toast(toast_msg)            

    def regular_get_data(self, dt):
        global flag_play
        global dt_no_antrian
        global count_starting, count_get_data
        global mydb
        global dt_load_l_value, dt_load_r_value, dt_brake_value
        
        try:
            if(count_starting > 0):
                count_starting -= 1              

            if(count_get_data > 0):
                count_get_data -= 1
                
            elif(count_get_data <= 0):
                flag_play = False
                Clock.unschedule(self.regular_get_data)

            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                axle_load_registers = MODBUS_CLIENT.read_holding_registers(1712, 2, slave=1) #V1200 - V1201
                brake_registers = MODBUS_CLIENT.read_holding_registers(1862, 1, slave=1) #V1350
                MODBUS_CLIENT.close()

                dt_load_l_value = axle_load_registers.registers[0]
                dt_load_r_value = axle_load_registers.registers[1]
                dt_brake_value = brake_registers.registers[0]
                
        except Exception as e:
            toast_msg = f'Error Get Data: {e}'
            print(toast_msg) 

    def regular_update_connection(self, dt):
        global flag_conn_stat

        try:
            MODBUS_CLIENT.connect()
            flag_conn_stat = MODBUS_CLIENT.connected
            MODBUS_CLIENT.close()
            
        except Exception as e:
            toast_msg = f'Error Update Connection: {e}'
            toast(toast_msg)   
            flag_conn_stat = False

    def exec_reload_table(self):
        global mydb, db_antrian
        try:
            mycursor = mydb.cursor()
            mycursor.execute(f"SELECT noantrian, nopol, nouji, user, idjeniskendaraan, load_flag, brake_flag FROM {TB_DATA}")
            myresult = mycursor.fetchall()
            mydb.commit()
            db_antrian = np.array(myresult).T

            layout_list = self.ids.layout_list
            layout_list.clear_widgets(children=None)

        except Exception as e:
            toast_msg = f'Error Remove Widget: {e}'
            print(toast_msg)
        
        try:           
            layout_list = self.ids.layout_list
            for i in range(db_antrian[0,:].size):
                layout_list.add_widget(
                    MDCard(
                        MDLabel(text=f"{i+1}", size_hint_x= 0.1),
                        MDLabel(text=f"{db_antrian[0, i]}", size_hint_x= 0.2),
                        MDLabel(text=f"{db_antrian[1, i]}", size_hint_x= 0.3),
                        MDLabel(text=f"{db_antrian[2, i]}", size_hint_x= 0.3),
                        MDLabel(text=f"{db_antrian[3, i]}", size_hint_x= 0.3),
                        MDLabel(text=f"{db_antrian[4, i]}", size_hint_x= 0.4),
                        MDLabel(text='Belum Tes' if (int(db_antrian[5, i]) == 0) else 'Lulus' if (int(db_antrian[5, i]) == 1) else 'Gagal', size_hint_x= 0.2),
                        MDLabel(text='Belum Tes' if (int(db_antrian[6, i]) == 0) else 'Lulus' if (int(db_antrian[6, i]) == 1) else 'Gagal', size_hint_x= 0.2),

                        ripple_behavior = True,
                        on_press = self.on_row_press,
                        padding = 10,
                        id=f"card{i}",
                        size_hint_y=None,
                        height="60dp",
                        )
                    )
                
        except Exception as e:
            toast_msg = f'Error Reload Table: {e}'
            print(toast_msg)

    def exec_start_load(self):
        global flag_play

        if(not flag_play):
            Clock.schedule_interval(self.regular_get_data, 1)
            self.open_screen_load()
            flag_play = True

    def open_screen_load(self):
        self.screen_manager.current = 'screen_load'

    def exec_start_brake(self):
        global flag_play

        if(not flag_play):
            Clock.schedule_interval(self.regular_get_data, 1)
            self.open_screen_brake()
            flag_play = True

    def open_screen_brake(self):
        self.screen_manager.current = 'screen_brake'

    def exec_logout(self):
        self.screen_manager.current = 'screen_login'

class ScreenLoad(MDScreen):        
    def __init__(self, **kwargs):
        super(ScreenLoad, self).__init__(**kwargs)
        Clock.schedule_once(self.delayed_init, 2)        

    def delayed_init(self, dt):
        pass

    def exec_start_load(self):
        global flag_play
        global count_starting, count_get_data

        screen_main = self.screen_manager.get_screen('screen_main')

        count_starting = COUNT_STARTING
        count_get_data = COUNT_ACQUISITION

        if(not flag_play):
            Clock.schedule_interval(screen_main.regular_get_data, 1)
            flag_play = True

    def exec_reload(self):
        global flag_play
        global count_starting, count_get_data, dt_load_l_value, dt_load_r_value

        screen_main = self.screen_manager.get_screen('screen_main')

        count_starting = COUNT_STARTING
        count_get_data = COUNT_ACQUISITION
        dt_load_l_value = 0
        dt_load_r_value = 0
        self.ids.bt_reload.disabled = True
        self.ids.lb_load_l_val.text = "..."
        self.ids.lb_load_r_val.text = " "

        if(not flag_play):
            Clock.schedule_interval(screen_main.regular_get_data, 1)
            flag_play = True

    def exec_save(self):
        global flag_play
        global count_starting, count_get_data
        global mydb, db_antrian
        global dt_no_antrian, dt_no_reg, dt_no_uji, dt_nama, dt_jenis_kendaraan
        global dt_load_flag, dt_load_l_value, dt_load_r_value, dt_load_user, dt_load_post

        self.ids.bt_save.disabled = True

        mycursor = mydb.cursor()

        sql = f"UPDATE {TB_DATA} SET load_flag = %s, load_l_value = %s, load_r_value = %s, load_user = %s, load_post = %s WHERE noantrian = %s"
        sql_load_flag = (1 if dt_load_flag == "Lulus" else 2)
        dt_load_post = str(time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()))
        print_datetime = str(time.strftime("%d %B %Y %H:%M:%S", time.localtime()))
        sql_val = (sql_load_flag, dt_load_l_value,dt_load_r_value, dt_load_user, dt_load_post, dt_no_antrian)
        mycursor.execute(sql, sql_val)
        mydb.commit()

        self.open_screen_main()

    def open_screen_main(self):
        global flag_play        
        global count_starting, count_get_data

        screen_main = self.screen_manager.get_screen('screen_main')

        count_starting = COUNT_STARTING
        count_get_data = COUNT_ACQUISITION
        flag_play = False   
        screen_main.exec_reload_table()
        self.screen_manager.current = 'screen_main'

    def exec_logout(self):
        self.screen_manager.current = 'screen_login'

class ScreenBrake(MDScreen):        
    def __init__(self, **kwargs):
        super(ScreenBrake, self).__init__(**kwargs)
        Clock.schedule_once(self.delayed_init, 2)
        
    def delayed_init(self, dt):
        pass

    def exec_start_brake(self):
        global flag_play
        global count_starting, count_get_data

        screen_main = self.screen_manager.get_screen('screen_main')

        count_starting = COUNT_STARTING
        count_get_data = COUNT_ACQUISITION

        if(not flag_play):
            Clock.schedule_interval(screen_main.regular_get_data, 1)
            flag_play = True

    def exec_reload(self):
        global flag_play
        global count_starting, count_get_data, dt_brake_value

        screen_main = self.screen_manager.get_screen('screen_main')

        count_starting = COUNT_STARTING
        count_get_data = COUNT_ACQUISITION
        dt_brake_value = 0
        self.ids.bt_reload.disabled = True
        self.ids.lb_brake_l_val.text = "..."
        self.ids.lb_brake_r_val.text = " "

        if(not flag_play):
            Clock.schedule_interval(screen_main.regular_get_data, 1)
            flag_play = True

    def exec_save(self):
        global flag_play
        global count_starting, count_get_data
        global mydb, db_antrian
        global dt_no_antrian, dt_no_reg, dt_no_uji, dt_nama, dt_jenis_kendaraan
        global dt_brake_flag, dt_brake_value, dt_brake_user, dt_brake_post

        self.ids.bt_save.disabled = True

        mycursor = mydb.cursor()

        sql = f"UPDATE {TB_DATA} SET brake_flag = %s, brake_value = %s, brake_user = %s, brake_post = %s WHERE noantrian = %s"
        sql_brake_flag = (1 if dt_brake_flag == "Lulus" else 2)
        dt_brake_post = str(time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()))
        print_datetime = str(time.strftime("%d %B %Y %H:%M:%S", time.localtime()))
        sql_val = (sql_brake_flag, dt_brake_value, dt_brake_user, dt_brake_post, dt_no_antrian)
        mycursor.execute(sql, sql_val)
        mydb.commit()

        self.open_screen_main()

    def open_screen_main(self):
        global flag_play        
        global count_starting, count_get_data

        screen_main = self.screen_manager.get_screen('screen_main')

        count_starting = COUNT_STARTING
        count_get_data = COUNT_ACQUISITION
        flag_play = False   
        screen_main.exec_reload_table()
        self.screen_manager.current = 'screen_main'

    def exec_logout(self):
        self.screen_manager.current = 'screen_login'

class RootScreen(ScreenManager):
    pass             

class LoadBrakeMeterApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def build(self):
        self.theme_cls.colors = colors
        self.theme_cls.primary_palette = "Gray"
        self.theme_cls.accent_palette = "Blue"
        self.theme_cls.theme_style = "Light"
        self.icon = 'assets/logo.png'

        LabelBase.register(
            name="Orbitron-Regular",
            fn_regular="assets/fonts/Orbitron-Regular.ttf")

        theme_font_styles.append('Display')
        self.theme_cls.font_styles["Display"] = [
            "Orbitron-Regular", 72, False, 0.15]       
        
        Window.fullscreen = 'auto'
        Builder.load_file('main.kv')
        return RootScreen()

if __name__ == '__main__':
    try:
        if hasattr(sys, '_MEIPASS'):
            resource_add_path(os.path.join(sys._MEIPASS))
        LoadBrakeMeterApp().run()
    except Exception as e:
        print(e)