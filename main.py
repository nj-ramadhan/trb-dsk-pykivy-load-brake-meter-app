from kivy.clock import Clock
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivymd.font_definitions import theme_font_styles
from kivymd.uix.datatables import MDDataTable
from kivy.uix.screenmanager import ScreenManager
from kivymd.uix.screen import MDScreen
from kivymd.app import MDApp
from kivy.metrics import dp
from kivymd.toast import toast
import numpy as np
import time
import mysql.connector
from escpos.printer import Serial as printerSerial
import configparser
import serial.tools.list_ports as ports
import hashlib
import serial
from pymodbus.client import ModbusTcpClient
from kivy.logger import Logger


colors = {
    "Red": {
        "A200": "#FF2A2A",
        "A500": "#FF8080",
        "A700": "#FFD5D5",
    },

    "Gray": {
        "200": "#CCCCCC",
        "500": "#ECECEC",
        "700": "#F9F9F9",
    },

    "Blue": {
        "200": "#4471C4",
        "500": "#5885D8",
        "700": "#6C99EC",
    },

    "Green": {
        "200": "#2CA02C", #41cd93
        "500": "#2DB97F",
        "700": "#D5FFD5",
    },

    "Yellow": {
        "200": "#ffD42A",
        "500": "#ffE680",
        "700": "#fff6D5",
    },

    "Light": {
        "StatusBar": "E0E0E0",
        "AppBar": "#202020",
        "Background": "#EEEEEE",
        "CardsDialogs": "#FFFFFF",
        "FlatButtonDown": "#CCCCCC",
    },

    "Dark": {
        "StatusBar": "101010",
        "AppBar": "#E0E0E0",
        "Background": "#111111",
        "CardsDialogs": "#222222",
        "FlatButtonDown": "#DDDDDD",
    },
}

#load credentials from config.ini
config = configparser.ConfigParser()
config.read('config.ini')
DB_HOST = config['mysql']['DB_HOST']
DB_USER = config['mysql']['DB_USER']
DB_PASSWORD = config['mysql']['DB_PASSWORD']
DB_NAME = config['mysql']['DB_NAME']
TB_LBS = config['mysql']['TB_LBS']
TB_USER = config['mysql']['TB_USER']

STANDARD_MAX_AXLE_LOAD = float(config['standard']['STANDARD_MAX_AXLE_LOAD']) # in kg
STANDARD_MAX_BRAKE = float(config['standard']['STANDARD_MAX_BRAKE']) # in kg
STANDARD_MIN_SPEED = float(config['standard']['STANDARD_MIN_SPEED']) # in rpm

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
dt_speed_value = 0
dt_speed_flag = 0
dt_speed_user = 1
dt_speed_post = str(time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()))

dt_user = "SILAHKAN LOGIN"
dt_no_antrian = ""
dt_no_reg = ""
dt_no_uji = ""
dt_nama = ""
dt_jenis_kendaraan = ""

modbus_client = ModbusTcpClient('192.168.1.111')

class ScreenLogin(MDScreen):
    def __init__(self, **kwargs):
        super(ScreenLogin, self).__init__(**kwargs)

    def exec_cancel(self):
        try:
            self.ids.tx_username.text = ""
            self.ids.tx_password.text = ""    

        except Exception as e:
            toast_msg = f'error Login: {e}'

    def exec_login(self):
        global mydb, db_users
        global dt_load_user, dt_user

        try:
            input_username = self.ids.tx_username.text
            input_password = self.ids.tx_password.text        
            # Adding salt at the last of the password
            dataBase_password = input_password
            # Encoding the password
            hashed_password = hashlib.md5(dataBase_password.encode())

            mycursor = mydb.cursor()
            mycursor.execute("SELECT id_user, nama, username, password, nama FROM users WHERE username = '"+str(input_username)+"' and password = '"+str(hashed_password.hexdigest())+"'")
            myresult = mycursor.fetchone()
            db_users = np.array(myresult).T
            #if invalid
            if myresult == 0:
                toast('Gagal Masuk, Nama Pengguna atau Password Salah')
            #else, if valid
            else:
                toast_msg = f'Berhasil Masuk, Selamat Datang {myresult[1]}'
                toast(toast_msg)
                dt_load_user = myresult[0]
                dt_user = myresult[1]
                self.ids.tx_username.text = ""
                self.ids.tx_password.text = "" 
                self.screen_manager.current = 'screen_main'

        except Exception as e:
            toast_msg = f'error Login: {e}'
            toast(toast_msg)        
            toast('Gagal Masuk, Nama Pengguna atau Password Salah')

class ScreenMain(MDScreen):   
    def __init__(self, **kwargs):
        super(ScreenMain, self).__init__(**kwargs)
        global mydb, db_antrian
        global flag_conn_stat, flag_play
        global count_starting, count_get_data

        Clock.schedule_once(self.delayed_init, 1)

        flag_conn_stat = False
        flag_play = False

        count_starting = 3
        count_get_data = 4
        try:
            mydb = mysql.connector.connect(
            host = DB_HOST,
            user = DB_USER,
            password = DB_PASSWORD,
            database = DB_NAME
            )

        except Exception as e:
            toast_msg = f'error initiate Database: {e}'
            toast(toast_msg)     
        
    def delayed_init(self, dt):
        Clock.schedule_interval(self.regular_update_connection, 5)
        Clock.schedule_interval(self.regular_update_display, 1)
        # Clock.schedule_interval(self.regular_highspeed_display, 0.5)
        layout = self.ids.layout_table
        
        self.data_tables = MDDataTable(
            use_pagination=True,
            pagination_menu_pos="auto",
            rows_num=10,
            column_data=[
                ("No.", dp(10), self.sort_on_num),
                ("Antrian", dp(20)),
                ("No. Reg", dp(25)),
                ("No. Uji", dp(35)),
                ("Nama", dp(35)),
                ("Jenis", dp(50)),
                ("Sts Load", dp(20)),
                ("Sts Brake", dp(20)),
                ("Sts Speed", dp(20)),
            ],
        )
        self.data_tables.bind(on_row_press=self.on_row_press)
        layout.add_widget(self.data_tables)
        self.exec_reload_table()


    def regular_update_connection(self, dt):
        global flag_conn_stat

        try:
            modbus_client.connect()
            flag_conn_stat = modbus_client.connected
            modbus_client.close()

            
        except Exception as e:
            toast_msg = f'{e}'
            toast(toast_msg)   
            flag_conn_stat = False

    def regular_get_data(self, dt):
        global count_starting, count_get_data
        global dt_load_l_value,dt_load_r_value,dt_speed_value, dt_brake_value
        global flag_play
        try:
            if(count_starting > 0):
                count_starting -= 1              

            if(count_get_data > 0):
                count_get_data -= 1
                
            elif(count_get_data <= 0):
                flag_play = False
                Clock.unschedule(self.regular_get_data)

            if flag_conn_stat:
                modbus_client.connect()
                axle_load_registers = modbus_client.read_holding_registers(1712, 2, slave=1) #V1200 - V1201
                speed_registers = modbus_client.read_holding_registers(1812, 1, slave=1) #V1360
                brake_registers = modbus_client.read_holding_registers(1812, 1, slave=1) #V1360
                modbus_client.close()

                dt_load_l_value = axle_load_registers.registers[0]
                dt_load_r_value = axle_load_registers.registers[1]
                dt_speed_value = speed_registers.registers[0]
                dt_brake_value = brake_registers.registers[0]
                
        except Exception as e:
            print(e)

    def sort_on_num(self, data):
        try:
            return zip(*sorted(enumerate(data),key=lambda l: l[0][0]))
        except:
            toast("Error sorting data")

    def on_row_press(self, table, row):
        global dt_no_antrian, dt_no_reg, dt_no_uji, dt_nama, dt_jenis_kendaraan
        global dt_load_flag, dt_load_l_value, dt_load_r_value, dt_load_user, dt_load_post
        global dt_brake_flag, dt_brake_value, dt_brake_user, dt_brake_post
        global dt_speed_flag, dt_speed_value, dt_speed_user, dt_speed_post

        try:
            start_index, end_index  = row.table.recycle_data[row.index]["range"]
            dt_no_antrian           = row.table.recycle_data[start_index + 1]["text"]
            dt_no_reg               = row.table.recycle_data[start_index + 2]["text"]
            dt_no_uji               = row.table.recycle_data[start_index + 3]["text"]
            dt_nama                 = row.table.recycle_data[start_index + 4]["text"]
            dt_jenis_kendaraan      = row.table.recycle_data[start_index + 5]["text"]
            dt_load_flag            = row.table.recycle_data[start_index + 6]["text"]
            dt_brake_flag           = row.table.recycle_data[start_index + 7]["text"]
            dt_speed_flag           = row.table.recycle_data[start_index + 8]["text"]

        except Exception as e:
            toast_msg = f'error update table: {e}'
            toast(toast_msg)   

    def regular_update_display(self, dt):
        global flag_conn_stat
        global count_starting, count_get_data
        global dt_user, dt_no_antrian, dt_no_reg, dt_no_uji, dt_nama, dt_jenis_kendaraan
        global dt_load_flag, dt_load_l_value, dt_load_r_value, dt_load_user, dt_load_post
        global dt_brake_flag, dt_brake_value, dt_brake_user, dt_brake_post
        global dt_speed_flag, dt_speed_value, dt_speed_user, dt_speed_post
        
        try:
            screen_login = self.screen_manager.get_screen('screen_login')
            screen_load = self.screen_manager.get_screen('screen_load')
            screen_brake = self.screen_manager.get_screen('screen_brake')
            screen_speed = self.screen_manager.get_screen('screen_speed')
            
            self.ids.lb_time.text = str(time.strftime("%H:%M:%S", time.localtime()))
            self.ids.lb_date.text = str(time.strftime("%d/%m/%Y", time.localtime()))
            screen_login.ids.lb_time.text = str(time.strftime("%H:%M:%S", time.localtime()))
            screen_login.ids.lb_date.text = str(time.strftime("%d/%m/%Y", time.localtime()))
            screen_load.ids.lb_time.text = str(time.strftime("%H:%M:%S", time.localtime()))
            screen_load.ids.lb_date.text = str(time.strftime("%d/%m/%Y", time.localtime()))
            screen_brake.ids.lb_time.text = str(time.strftime("%H:%M:%S", time.localtime()))
            screen_brake.ids.lb_date.text = str(time.strftime("%d/%m/%Y", time.localtime()))
            screen_speed.ids.lb_time.text = str(time.strftime("%H:%M:%S", time.localtime()))
            screen_speed.ids.lb_date.text = str(time.strftime("%d/%m/%Y", time.localtime()))

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

            screen_speed.ids.lb_no_antrian.text = str(dt_no_antrian)
            screen_speed.ids.lb_no_reg.text = str(dt_no_reg)
            screen_speed.ids.lb_no_uji.text = str(dt_no_uji)
            screen_speed.ids.lb_nama.text = str(dt_nama)
            screen_speed.ids.lb_jenis_kendaraan.text = str(dt_jenis_kendaraan)

            screen_load.ids.lb_load_l_val.text = str(dt_load_l_value)
            screen_load.ids.lb_load_r_val.text = str(dt_load_r_value)
            screen_brake.ids.lb_brake_val.text = str(dt_brake_value)
            screen_speed.ids.lb_speed_val.text = str(dt_speed_value)

            if(dt_load_flag == "Belum Tes"):
                self.ids.bt_start_load.disabled = False
            else:
                self.ids.bt_start_load.disabled = True

            if(dt_brake_flag == "Belum Tes"):
                self.ids.bt_start_brake.disabled = False
            else:
                self.ids.bt_start_brake.disabled = True

            if(dt_speed_flag == "Belum Tes"):
                self.ids.bt_start_speed.disabled = False
            else:
                self.ids.bt_start_speed.disabled = True

            if(not flag_play):
                screen_load.ids.bt_save.md_bg_color = colors['Green']['200']
                screen_load.ids.bt_save.disabled = False
                screen_load.ids.bt_reload.md_bg_color = colors['Red']['A200']
                screen_load.ids.bt_reload.disabled = False

                screen_brake.ids.bt_save.md_bg_color = colors['Green']['200']
                screen_brake.ids.bt_save.disabled = False
                screen_brake.ids.bt_reload.md_bg_color = colors['Red']['A200']
                screen_brake.ids.bt_reload.disabled = False

                screen_speed.ids.bt_save.md_bg_color = colors['Green']['200']
                screen_speed.ids.bt_save.disabled = False
                screen_speed.ids.bt_reload.md_bg_color = colors['Red']['A200']
                screen_speed.ids.bt_reload.disabled = False                
            else:
                screen_load.ids.bt_reload.disabled = True
                screen_load.ids.bt_save.disabled = True

                screen_brake.ids.bt_reload.disabled = True
                screen_brake.ids.bt_save.disabled = True

                screen_speed.ids.bt_reload.disabled = True
                screen_speed.ids.bt_save.disabled = True

            if(not flag_conn_stat):
                self.ids.lb_comm.color = colors['Red']['A200']
                self.ids.lb_comm.text = 'PLC Tidak Terhubung'
                screen_login.ids.lb_comm.color = colors['Red']['A200']
                screen_login.ids.lb_comm.text = 'PLC Tidak Terhubung'
                screen_load.ids.lb_comm.color = colors['Red']['A200']
                screen_load.ids.lb_comm.text = 'PLC Tidak Terhubung'
                screen_brake.ids.lb_comm.color = colors['Red']['A200']
                screen_brake.ids.lb_comm.text = 'PLC Tidak Terhubung'
                screen_speed.ids.lb_comm.color = colors['Red']['A200']
                screen_speed.ids.lb_comm.text = 'PLC Tidak Terhubung'

            else:
                self.ids.lb_comm.color = colors['Blue']['200']
                self.ids.lb_comm.text = 'PLC Terhubung'
                screen_login.ids.lb_comm.color = colors['Blue']['200']
                screen_login.ids.lb_comm.text = 'PLC Terhubung'
                screen_load.ids.lb_comm.color = colors['Blue']['200']
                screen_load.ids.lb_comm.text = 'PLC Terhubung'
                screen_brake.ids.lb_comm.color = colors['Blue']['200']
                screen_brake.ids.lb_comm.text = 'PLC Terhubung'
                screen_speed.ids.lb_comm.color = colors['Blue']['200']
                screen_speed.ids.lb_comm.text = 'PLC Terhubung'

            if(count_starting <= 0):
                screen_load.ids.lb_test_subtitle.text = "HASIL PENGUKURAN"
                screen_load.ids.lb_load_l_val.text = str(np.round(dt_load_l_value, 2))
                screen_load.ids.lb_load_r_val.text = str(np.round(dt_load_r_value, 2))

                screen_brake.ids.lb_test_subtitle.text = "HASIL PENGUKURAN"
                screen_brake.ids.lb_brake_val.text = str(np.round(dt_brake_value, 2))

                screen_speed.ids.lb_test_subtitle.text = "HASIL PENGUKURAN"
                screen_speed.ids.lb_speed_val.text = str(np.round(dt_speed_value, 2))

            elif(count_starting > 0):
                if(flag_play):
                    screen_load.ids.lb_test_subtitle.text = "MEMULAI PENGUKURAN"
                    screen_load.ids.lb_load_l_val.text = str(count_starting)
                    screen_load.ids.lb_load_r_val.text = "..."
                    screen_load.ids.lb_info.text = "Silahkan Tempatkan Kendaraan Anda Pada Tempat yang Sudah Disediakan"

                    screen_brake.ids.lb_test_subtitle.text = "MEMULAI PENGUKURAN"
                    screen_brake.ids.lb_brake_val.text = str(count_starting)
                    screen_brake.ids.lb_info.text = "Silahkan Tempatkan Kendaraan Anda Pada Tempat yang Sudah Disediakan"

                    screen_speed.ids.lb_test_subtitle.text = "MEMULAI PENGUKURAN"
                    screen_speed.ids.lb_speed_val.text = str(count_starting)
                    screen_speed.ids.lb_info.text = "Silahkan Injak Pedal Gas Sesuai Arahan"

            if(dt_load_l_value <= STANDARD_MAX_AXLE_LOAD):
                screen_load.ids.lb_info.text = "Berat Roda Kendaraan Anda Dalam Range Ambang Batas"
            else:
                screen_load.ids.lb_info.text = "Berat Roda Kendaraan Anda Diluar Ambang Batas"

            if(dt_brake_value <= STANDARD_MAX_BRAKE):
                screen_brake.ids.lb_info.text = "Kekuatan Pengereman Kendaraan Anda Dalam Range Ambang Batas"
            else:
                screen_brake.ids.lb_info.text = "Kekuatan Pengereman Kendaraan Anda Diluar Ambang Batas"

            if(dt_speed_value >= STANDARD_MIN_SPEED):
                screen_speed.ids.lb_info.text = "Deviasi Kecepatan Kendaraan Anda Dalam Range Ambang Batas"
            else:
                screen_speed.ids.lb_info.text = "Deviasi Kecepatan Kendaraan Anda Diluar Ambang Batas"

            if(count_get_data <= 0):
                if(not flag_play):
                    screen_load.ids.lb_test_result.size_hint_y = 0.25
                    screen_brake.ids.lb_test_result.size_hint_y = 0.25
                    screen_speed.ids.lb_test_result.size_hint_y = 0.25
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

                    if(dt_speed_value >= STANDARD_MIN_SPEED):
                        screen_speed.ids.lb_test_result.md_bg_color = colors['Green']['200']
                        screen_speed.ids.lb_test_result.text = "LULUS"
                        dt_speed_flag = "Lulus"
                        screen_speed.ids.lb_test_result.text_color = colors['Green']['700']
                    else:
                        screen_speed.ids.lb_test_result.md_bg_color = colors['Red']['A200']
                        screen_speed.ids.lb_test_result.text = "TIDAK LULUS"
                        dt_speed_flag = "Tidak Lulus"
                        screen_speed.ids.lb_test_result.text_color = colors['Red']['A700']

            elif(count_get_data > 0):
                screen_load.ids.lb_test_result.md_bg_color = "#EEEEEE"
                screen_load.ids.lb_test_result.text = ""

                screen_brake.ids.lb_test_result.md_bg_color = "#EEEEEE"
                screen_brake.ids.lb_test_result.text = ""

                screen_speed.ids.lb_test_result.md_bg_color = "#EEEEEE"
                screen_speed.ids.lb_test_result.text = ""

                screen_load.ids.lb_info.text = f"Ambang Batas Beban yang diperbolehkan adalah {STANDARD_MAX_AXLE_LOAD} kg"
                screen_brake.ids.lb_info.text = f"Ambang Batas Rem yang diperbolehkan adalah {STANDARD_MAX_BRAKE} kg"
                screen_speed.ids.lb_info.text = f"Ambang Batas Kecepatan yang diperbolehkan adalah {STANDARD_MIN_SPEED} rpm"

            self.ids.lb_operator.text = dt_user
            screen_login.ids.lb_operator.text = dt_user
            screen_load.ids.lb_operator.text = dt_user
            screen_brake.ids.lb_operator.text = dt_user
            screen_speed.ids.lb_operator.text = dt_user

        except Exception as e:
            toast_msg = f'error update display: {e}'
            toast(toast_msg)                

    def exec_reload_table(self):
        global mydb, db_antrian
        try:
            mycursor = mydb.cursor()
            mycursor.execute("SELECT noantrian, nopol, nouji, user, idjeniskendaraan, load_flag, brake_flag, speed_flag FROM tb_cekident")
            myresult = mycursor.fetchall()
            db_antrian = np.array(myresult).T

            self.data_tables.row_data=[(f"{i+1}", f"{db_antrian[0, i]}", f"{db_antrian[1, i]}", f"{db_antrian[2, i]}", f"{db_antrian[3, i]}" ,f"{db_antrian[4, i]}", 
                                        'Belum Tes' if (int(db_antrian[5, i]) == 0) else ('Lulus' if (int(db_antrian[5, i]) == 1) else 'Tidak Lulus'),
                                        'Belum Tes' if (int(db_antrian[6, i]) == 0) else ('Lulus' if (int(db_antrian[6, i]) == 1) else 'Tidak Lulus'),
                                        'Belum Tes' if (int(db_antrian[7, i]) == 0) else ('Lulus' if (int(db_antrian[7, i]) == 1) else 'Tidak Lulus')) 
                                        for i in range(len(db_antrian[0]))]

        except Exception as e:
            toast_msg = f'error reload table: {e}'
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

    def exec_start_speed(self):
        global flag_play

        if(not flag_play):
            Clock.schedule_interval(self.regular_get_data, 1)
            self.open_screen_speed()
            flag_play = True

    def open_screen_speed(self):
        self.screen_manager.current = 'screen_speed'

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

        count_starting = 3
        count_get_data = 10

        if(not flag_play):
            Clock.schedule_interval(screen_main.regular_get_data, 1)
            flag_play = True

    def exec_reload(self):
        global flag_play
        global count_starting, count_get_data, dt_load_l_value, dt_load_r_value

        screen_main = self.screen_manager.get_screen('screen_main')

        count_starting = 3
        count_get_data = 10
        dt_load_l_value = 0
        dt_load_r_value = 0
        self.ids.bt_reload.disabled = True
        self.ids.lb_load_l_val.text = "..."
        self.ids.lb_load_r_val.text = "..."

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

        sql = "UPDATE tb_cekident SET load_flag = %s, load_l_value = %s, load_r_value = %s, load_user = %s, load_post = %s WHERE noantrian = %s"
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

        count_starting = 3
        count_get_data = 10
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

        count_starting = 3
        count_get_data = 10

        if(not flag_play):
            Clock.schedule_interval(screen_main.regular_get_data, 1)
            flag_play = True

    def exec_reload(self):
        global flag_play
        global count_starting, count_get_data, dt_brake_value

        screen_main = self.screen_manager.get_screen('screen_main')

        count_starting = 3
        count_get_data = 10
        dt_brake_value = 0
        self.ids.bt_reload.disabled = True
        self.ids.lb_brake_val.text = "..."

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

        sql = "UPDATE tb_cekident SET brake_flag = %s, brake_value = %s, brake_user = %s, brake_post = %s WHERE noantrian = %s"
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

        count_starting = 3
        count_get_data = 10
        flag_play = False   
        screen_main.exec_reload_table()
        self.screen_manager.current = 'screen_main'

    def exec_logout(self):
        self.screen_manager.current = 'screen_login'

class ScreenSpeed(MDScreen):        
    def __init__(self, **kwargs):
        super(ScreenSpeed, self).__init__(**kwargs)
        Clock.schedule_once(self.delayed_init, 2)
        
    def delayed_init(self, dt):
        pass

    def exec_start_speed(self):
        global flag_play
        global count_starting, count_get_data

        screen_main = self.screen_manager.get_screen('screen_main')

        count_starting = 3
        count_get_data = 10

        if(not flag_play):
            Clock.schedule_interval(screen_main.regular_get_data, 1)
            flag_play = True

    def exec_reload(self):
        global flag_play
        global count_starting, count_get_data, dt_speed_value

        screen_main = self.screen_manager.get_screen('screen_main')

        count_starting = 3
        count_get_data = 10
        dt_speed_value = 0
        self.ids.bt_reload.disabled = True
        self.ids.lb_speed_val.text = "..."

        if(not flag_play):
            Clock.schedule_interval(screen_main.regular_get_data, 1)
            flag_play = True

    def exec_save(self):
        global flag_play
        global count_starting, count_get_data
        global mydb, db_antrian
        global dt_no_antrian, dt_no_reg, dt_no_uji, dt_nama, dt_jenis_kendaraan
        global dt_speed_flag, dt_speed_value, dt_speed_user, dt_speed_post

        self.ids.bt_save.disabled = True

        mycursor = mydb.cursor()

        sql = "UPDATE tb_cekident SET speed_flag = %s, speed_value = %s, speed_user = %s, speed_post = %s WHERE noantrian = %s"
        sql_speed_flag = (1 if dt_speed_flag == "Lulus" else 2)
        dt_speed_post = str(time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()))
        print_datetime = str(time.strftime("%d %B %Y %H:%M:%S", time.localtime()))
        sql_val = (sql_speed_flag, dt_speed_value, dt_speed_user, dt_speed_post, dt_no_antrian)
        mycursor.execute(sql, sql_val)
        mydb.commit()

        self.open_screen_main()

    def open_screen_main(self):
        global flag_play        
        global count_starting, count_get_data

        screen_main = self.screen_manager.get_screen('screen_main')

        count_starting = 3
        count_get_data = 10
        flag_play = False   
        screen_main.exec_reload_table()
        self.screen_manager.current = 'screen_main'

    def exec_logout(self):
        self.screen_manager.current = 'screen_login'


class RootScreen(ScreenManager):
    pass             

class LoadBrakeSpeedMeterApp(MDApp):
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
        # Window.borderless = False
        # Window.size = 900, 1440
        # Window.size = 450, 720
        # Window.allow_screensaver = True

        Builder.load_file('main.kv')
        return RootScreen()

if __name__ == '__main__':
    LoadBrakeSpeedMeterApp().run()