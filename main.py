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

config_name = 'config.ini'
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
    running_mode = 'Frozen/executable'
else:
    try:
        app_full_path = os.path.realpath(__file__)
        application_path = os.path.dirname(app_full_path)
        running_mode = "Non-interactive (e.g. 'python myapp.py')"
    except NameError:
        application_path = os.getcwd()
        running_mode = 'Interactive'

config_full_path = os.path.join(application_path, config_name)
config = configparser.ConfigParser()
config.read(config_full_path)

# SQL setting
DB_HOST = config['mysql']['DB_HOST']
DB_USER = config['mysql']['DB_USER']
DB_PASSWORD = config['mysql']['DB_PASSWORD']
DB_NAME = config['mysql']['DB_NAME']
TB_DATA = config['mysql']['TB_DATA']
TB_USER = config['mysql']['TB_USER']
TB_MERK = config['mysql']['TB_MERK']

# system setting
TIME_OUT = int(config['setting']['TIME_OUT'])
COUNT_STARTING = int(config['setting']['COUNT_STARTING'])
COUNT_ACQUISITION = int(config['setting']['COUNT_ACQUISITION'])
UPDATE_CAROUSEL_INTERVAL = float(config['setting']['UPDATE_CAROUSEL_INTERVAL'])
UPDATE_CONNECTION_INTERVAL = float(config['setting']['UPDATE_CONNECTION_INTERVAL'])
GET_DATA_INTERVAL = float(config['setting']['GET_DATA_INTERVAL'])

MODBUS_IP_PLC = config['setting']['MODBUS_IP_PLC']
MODBUS_CLIENT = ModbusTcpClient(MODBUS_IP_PLC)
REGISTER_DATA_LOAD = int(config['setting']['REGISTER_DATA_LOAD'])
REGISTER_DATA_BRAKE = int(config['setting']['REGISTER_DATA_BRAKE'])

# system standard
STANDARD_MAX_AXLE_LOAD = float(config['standard']['STANDARD_MAX_AXLE_LOAD']) # in kg
STANDARD_MAX_BRAKE = float(config['standard']['STANDARD_MAX_BRAKE']) # %

db_load_left_value = np.zeros(10, dtype=float)
db_load_right_value = np.zeros(10, dtype=float)
db_load_total_value = np.zeros(10, dtype=float)
dt_load_total_value = 0
dt_load_flag = 0
dt_load_user = 1
dt_load_post = str(time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()))

db_brake_left_value = np.zeros(10, dtype=float)
db_brake_right_value = np.zeros(10, dtype=float)
db_brake_total_value = np.zeros(10, dtype=float)
db_brake_efficiency_value = np.zeros(10, dtype=float)
db_brake_difference_value = np.zeros(10, dtype=float)
dt_brake_total_value = 0
dt_brake_efficiency_value = 0
dt_brake_difference_value = 0
dt_brake_flag = 0
dt_brake_user = 1
dt_brake_post = str(time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()))

db_handbrake_left_value = np.zeros(10, dtype=float)
db_handbrake_right_value = np.zeros(10, dtype=float)
db_handbrake_total_value = np.zeros(10, dtype=float)
db_handbrake_efficiency_value = np.zeros(10, dtype=float)
db_handbrake_difference_value = np.zeros(10, dtype=float)
dt_handbrake_total_value = 0
dt_handbrake_efficiency_value = 0
dt_handbrake_difference_value = 0
dt_handbrake_flag = 0
dt_handbrake_user = 1
dt_handbrake_post = str(time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()))

dt_user = ""
dt_no_antrian = ""
dt_no_pol = ""
dt_no_uji = ""
dt_nama = ""
dt_jenis_kendaraan = ""

dt_test_number = 0
dt_dash_pendaftaran = 0
dt_dash_belum_uji = 0
dt_dash_sudah_uji = 0

flag_cylinder = False

class ScreenHome(MDScreen):
    def __init__(self, **kwargs):
        super(ScreenHome, self).__init__(**kwargs)
        Clock.schedule_once(self.delayed_init, 1)

    def delayed_init(self, dt):
        Clock.schedule_interval(self.regular_update_carousel, UPDATE_CAROUSEL_INTERVAL)

    def regular_update_carousel(self, dt):
        try:
            self.ids.carousel.index += 1
            
        except Exception as e:
            toast_msg = f'Error Update Display: {e}'
            toast(toast_msg)                

    def exec_navigate_home(self):
        try:
            self.screen_manager.current = 'screen_home'

        except Exception as e:
            toast_msg = f'Error Navigate to Home Screen: {e}'
            toast(toast_msg)        

    def exec_navigate_login(self):
        global dt_user
        try:
            if (dt_user == ""):
                self.screen_manager.current = 'screen_login'
            else:
                toast(f"Anda sudah login sebagai {dt_user}")

        except Exception as e:
            toast_msg = f'Error Navigate to Login Screen: {e}'
            toast(toast_msg)     

    def exec_navigate_main(self):
        try:
            self.screen_manager.current = 'screen_main'

        except Exception as e:
            toast_msg = f'Error Navigate to Main Screen: {e}'
            toast(toast_msg)    

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
        global dt_check_user, dt_user

        screen_main = self.screen_manager.get_screen('screen_main')

        try:
            screen_main.exec_reload_database()
            input_username = self.ids.tx_username.text
            input_password = self.ids.tx_password.text        
            # Adding salt at the last of the password
            dataBase_password = input_password
            # Encoding the password
            hashed_password = hashlib.md5(dataBase_password.encode())

            mycursor = mydb.cursor()
            mycursor.execute(f"SELECT id_user, nama, username, password, nama FROM {TB_USER} WHERE username = '{input_username}' and password = '{hashed_password.hexdigest()}'")
            myresult = mycursor.fetchone()
            db_users = np.array(myresult).T
            #if invalid
            if myresult == 0:
                toast('Gagal Masuk, Nama Pengguna atau Password Salah')
            #else, if valid
            else:
                toast_msg = f'Berhasil Masuk, Selamat Datang {myresult[1]}'
                toast(toast_msg)
                dt_check_user = myresult[0]
                dt_user = myresult[1]
                self.ids.tx_username.text = ""
                self.ids.tx_password.text = "" 
                self.screen_manager.current = 'screen_main'

        except Exception as e:
            toast_msg = f'error Login: {e}'
            toast(toast_msg)        
            toast('Gagal Masuk, Nama Pengguna atau Password Salah')

    def exec_navigate_home(self):
        try:
            self.screen_manager.current = 'screen_home'

        except Exception as e:
            toast_msg = f'Error Navigate to Home Screen: {e}'
            toast(toast_msg)        

    def exec_navigate_login(self):
        global dt_user
        try:
            if (dt_user == ""):
                self.screen_manager.current = 'screen_login'
            else:
                toast(f"Anda sudah login sebagai {dt_user}")

        except Exception as e:
            toast_msg = f'Error Navigate to Login Screen: {e}'
            toast(toast_msg)     

    def exec_navigate_main(self):
        try:
            self.screen_manager.current = 'screen_main'

        except Exception as e:
            toast_msg = f'Error Navigate to Main Screen: {e}'
            toast(toast_msg)   

class ScreenMain(MDScreen):   
    def __init__(self, **kwargs):
        super(ScreenMain, self).__init__(**kwargs)
        Clock.schedule_once(self.delayed_init, 1)                 

    def delayed_init(self, dt):
        global flag_conn_stat, flag_play
        global count_starting, count_get_data

        flag_conn_stat = False
        flag_play = False

        count_starting = COUNT_STARTING
        count_get_data = COUNT_ACQUISITION
        
        Clock.schedule_interval(self.regular_update_display, 1)
        Clock.schedule_interval(self.regular_update_connection, UPDATE_CONNECTION_INTERVAL)
        self.exec_reload_database()
        self.exec_reload_table()

    def on_antrian_row_press(self, instance):
        global dt_no_antrian, dt_no_pol, dt_no_uji, dt_nama, dt_load_flag, dt_brake_flag, dt_handbrake_flag
        global dt_merk, dt_type, dt_jenis_kendaraan, dt_jbb, dt_bahan_bakar, dt_warna
        global db_antrian, db_merk

        try:
            row = int(str(instance.id).replace("card_antrian",""))
            dt_no_antrian           = f"{db_antrian[0, row]}"
            dt_no_pol               = f"{db_antrian[1, row]}"
            dt_no_uji               = f"{db_antrian[2, row]}"
            dt_load_flag            = 'Belum Tes' if (int(db_antrian[3, row]) == 0) else 'Sudah Tes'
            dt_brake_flag           = 'Belum Tes' if (int(db_antrian[4, row]) == 0) else 'Sudah Tes'
            dt_handbrake_flag       = 'Belum Tes' if (int(db_antrian[5, row]) == 0) else 'Sudah Tes'
            dt_nama                 = f"{db_antrian[6, row]}"
            dt_merk                 = f"{db_merk[np.where(db_merk == db_antrian[7, row])[0][0],1]}"
            dt_type                 = f"{db_antrian[8, row]}"
            dt_jenis_kendaraan      = f"{db_antrian[9, row]}"
            dt_jbb                  = f"{db_antrian[10, row]}"
            dt_bahan_bakar          = f"{db_antrian[11, row]}"
            dt_warna                = f"{db_antrian[12, row]}"
                        
            self.exec_start()

        except Exception as e:
            toast_msg = f'Error Execute Command from Table Row: {e}'
            toast(toast_msg)   

    def regular_update_display(self, dt):
        global flag_conn_stat
        global count_starting, count_get_data
        global dt_user, dt_no_antrian, dt_no_pol, dt_no_uji, dt_nama, dt_jenis_kendaraan
        global dt_load_flag, db_load_left_value, db_load_right_value, db_load_total_value, dt_load_user, dt_load_post
        global dt_brake_flag, db_brake_left_value, db_brake_right_value, db_brake_total_value, db_brake_efficiency_value, db_brake_difference_value, dt_brake_user, dt_brake_post
        global dt_handbrake_flag, db_handbrake_left_value, db_handbrake_right_value, db_handbrake_total_value, db_handbrake_efficiency_value, db_handbrake_difference_value, dt_handbrake_user, dt_handbrake_post
        global dt_load_total_value, dt_brake_total_value, dt_brake_efficiency_value, dt_brake_difference_value, dt_handbrake_total_value, dt_handbrake_efficiency_value, dt_handbrake_difference_value
        global dt_test_number
        
        try:
            screen_home = self.screen_manager.get_screen('screen_home')
            screen_login = self.screen_manager.get_screen('screen_login')
            screen_menu = self.screen_manager.get_screen('screen_menu')
            screen_load_meter = self.screen_manager.get_screen('screen_load_meter')
            screen_brake_meter = self.screen_manager.get_screen('screen_brake_meter')
            screen_handbrake_meter = self.screen_manager.get_screen('screen_handbrake_meter')
            screen_resume = self.screen_manager.get_screen('screen_resume')
            
            self.ids.lb_time.text = str(time.strftime("%H:%M:%S", time.localtime()))
            self.ids.lb_date.text = str(time.strftime("%d/%m/%Y", time.localtime()))
            screen_home.ids.lb_time.text = str(time.strftime("%H:%M:%S", time.localtime()))
            screen_home.ids.lb_date.text = str(time.strftime("%d/%m/%Y", time.localtime()))
            screen_login.ids.lb_time.text = str(time.strftime("%H:%M:%S", time.localtime()))
            screen_login.ids.lb_date.text = str(time.strftime("%d/%m/%Y", time.localtime()))
            screen_menu.ids.lb_time.text = str(time.strftime("%H:%M:%S", time.localtime()))
            screen_menu.ids.lb_date.text = str(time.strftime("%d/%m/%Y", time.localtime()))
            screen_load_meter.ids.lb_time.text = str(time.strftime("%H:%M:%S", time.localtime()))
            screen_load_meter.ids.lb_date.text = str(time.strftime("%d/%m/%Y", time.localtime()))
            screen_brake_meter.ids.lb_time.text = str(time.strftime("%H:%M:%S", time.localtime()))
            screen_brake_meter.ids.lb_date.text = str(time.strftime("%d/%m/%Y", time.localtime()))
            screen_handbrake_meter.ids.lb_time.text = str(time.strftime("%H:%M:%S", time.localtime()))
            screen_handbrake_meter.ids.lb_date.text = str(time.strftime("%d/%m/%Y", time.localtime()))
            screen_resume.ids.lb_time.text = str(time.strftime("%H:%M:%S", time.localtime()))
            screen_resume.ids.lb_date.text = str(time.strftime("%d/%m/%Y", time.localtime()))

            self.ids.lb_dash_pendaftaran.text = str(dt_dash_pendaftaran)
            self.ids.lb_dash_belum_uji.text = str(dt_dash_belum_uji)
            self.ids.lb_dash_sudah_uji.text = str(dt_dash_sudah_uji)

            screen_menu.ids.lb_no_antrian.text = str(dt_no_antrian)
            screen_menu.ids.lb_no_pol.text = str(dt_no_pol)
            screen_menu.ids.lb_no_uji.text = str(dt_no_uji)
            screen_menu.ids.lb_nama.text = str(dt_nama)
            screen_menu.ids.lb_jenis_kendaraan.text = str(dt_jenis_kendaraan)

            screen_resume.ids.lb_no_antrian.text = str(dt_no_antrian)
            screen_resume.ids.lb_no_pol.text = str(dt_no_pol)
            screen_resume.ids.lb_no_uji.text = str(dt_no_uji)
            screen_resume.ids.lb_nama.text = str(dt_nama)
            screen_resume.ids.lb_jenis_kendaraan.text = str(dt_jenis_kendaraan)

            screen_load_meter.ids.lb_no_antrian.text = str(dt_no_antrian)
            screen_load_meter.ids.lb_no_pol.text = str(dt_no_pol)
            screen_load_meter.ids.lb_no_uji.text = str(dt_no_uji)
            screen_load_meter.ids.lb_nama.text = str(dt_nama)
            screen_load_meter.ids.lb_jenis_kendaraan.text = str(dt_jenis_kendaraan)

            screen_brake_meter.ids.lb_no_antrian.text = str(dt_no_antrian)
            screen_brake_meter.ids.lb_no_pol.text = str(dt_no_pol)
            screen_brake_meter.ids.lb_no_uji.text = str(dt_no_uji)
            screen_brake_meter.ids.lb_nama.text = str(dt_nama)
            screen_brake_meter.ids.lb_jenis_kendaraan.text = str(dt_jenis_kendaraan)

            screen_handbrake_meter.ids.lb_no_antrian.text = str(dt_no_antrian)
            screen_handbrake_meter.ids.lb_no_pol.text = str(dt_no_pol)
            screen_handbrake_meter.ids.lb_no_uji.text = str(dt_no_uji)
            screen_handbrake_meter.ids.lb_nama.text = str(dt_nama)
            screen_handbrake_meter.ids.lb_jenis_kendaraan.text = str(dt_jenis_kendaraan)

            screen_load_meter.ids.lb_load_l_val.text = str(db_load_left_value[dt_test_number])
            screen_load_meter.ids.lb_load_r_val.text = str(db_load_right_value[dt_test_number])
            screen_load_meter.ids.lb_load_total_val.text = str(db_load_total_value[dt_test_number])
            screen_brake_meter.ids.lb_brake_l_val.text = str(db_brake_left_value[dt_test_number])
            screen_brake_meter.ids.lb_brake_r_val.text = str(db_brake_right_value[dt_test_number])
            screen_brake_meter.ids.lb_brake_total_val.text = str(db_brake_total_value[dt_test_number])
            screen_handbrake_meter.ids.lb_handbrake_l_val.text = str(db_handbrake_left_value[dt_test_number])
            screen_handbrake_meter.ids.lb_handbrake_r_val.text = str(db_handbrake_right_value[dt_test_number])
            screen_handbrake_meter.ids.lb_handbrake_total_val.text = str(db_handbrake_total_value[dt_test_number])

            if(not flag_play):
                screen_resume.ids.bt_save.md_bg_color = colors['Green']['200']
                screen_resume.ids.bt_save.disabled = False
                screen_load_meter.ids.bt_reload.md_bg_color = colors['Red']['A200']
                screen_load_meter.ids.bt_reload.disabled = False
                screen_brake_meter.ids.bt_reload.md_bg_color = colors['Red']['A200']
                screen_brake_meter.ids.bt_reload.disabled = False
                screen_handbrake_meter.ids.bt_reload.md_bg_color = colors['Red']['A200']
                screen_handbrake_meter.ids.bt_reload.disabled = False
                    
            else:
                screen_resume.ids.bt_save.disabled = True
                screen_load_meter.ids.bt_reload.disabled = True
                screen_brake_meter.ids.bt_reload.disabled = True
                screen_handbrake_meter.ids.bt_reload.disabled = True

            if(not flag_conn_stat):
                self.ids.lb_comm.color = colors['Red']['A200']
                self.ids.lb_comm.text = 'PLC Tidak Terhubung'
                screen_home.ids.lb_comm.color = colors['Red']['A200']
                screen_home.ids.lb_comm.text = 'PLC Tidak Terhubung'
                screen_login.ids.lb_comm.color = colors['Red']['A200']
                screen_login.ids.lb_comm.text = 'PLC Tidak Terhubung'
                screen_load_meter.ids.lb_comm.color = colors['Red']['A200']
                screen_load_meter.ids.lb_comm.text = 'PLC Tidak Terhubung'
                screen_brake_meter.ids.lb_comm.color = colors['Red']['A200']
                screen_brake_meter.ids.lb_comm.text = 'PLC Tidak Terhubung'
                screen_handbrake_meter.ids.lb_comm.color = colors['Red']['A200']
                screen_handbrake_meter.ids.lb_comm.text = 'PLC Tidak Terhubung'

            else:
                self.ids.lb_comm.color = colors['Blue']['200']
                self.ids.lb_comm.text = 'PLC Terhubung'
                screen_home.ids.lb_comm.color = colors['Blue']['200']
                screen_home.ids.lb_comm.text = 'PLC Terhubung'
                screen_login.ids.lb_comm.color = colors['Blue']['200']
                screen_login.ids.lb_comm.text = 'PLC Terhubung'
                screen_load_meter.ids.lb_comm.color = colors['Blue']['200']
                screen_load_meter.ids.lb_comm.text = 'PLC Terhubung'
                screen_brake_meter.ids.lb_comm.color = colors['Blue']['200']
                screen_brake_meter.ids.lb_comm.text = 'PLC Terhubung'
                screen_handbrake_meter.ids.lb_comm.color = colors['Blue']['200']
                screen_handbrake_meter.ids.lb_comm.text = 'PLC Terhubung'

            if(count_starting <= 0):
                screen_load_meter.ids.lb_test_subtitle.text = "HASIL PENGUKURAN"
                screen_load_meter.ids.lb_load_l_val.text = str(db_load_left_value[dt_test_number])
                screen_load_meter.ids.lb_load_r_val.text = str(db_load_right_value[dt_test_number])
                screen_load_meter.ids.lb_load_total_val.text = str(db_load_total_value[dt_test_number])
                screen_brake_meter.ids.lb_test_subtitle.text = "HASIL PENGUKURAN"
                screen_brake_meter.ids.lb_brake_l_val.text = str(db_brake_left_value[dt_test_number])
                screen_brake_meter.ids.lb_brake_r_val.text = str(db_brake_right_value[dt_test_number])
                screen_brake_meter.ids.lb_brake_total_val.text = str(db_brake_total_value[dt_test_number])
                screen_handbrake_meter.ids.lb_test_subtitle.text = "HASIL PENGUKURAN"
                screen_handbrake_meter.ids.lb_handbrake_l_val.text = str(db_handbrake_left_value[dt_test_number])
                screen_handbrake_meter.ids.lb_handbrake_r_val.text = str(db_handbrake_right_value[dt_test_number])
                screen_handbrake_meter.ids.lb_handbrake_total_val.text = str(db_handbrake_total_value[dt_test_number])

                if(db_load_total_value[dt_test_number] <= STANDARD_MAX_AXLE_LOAD):
                    screen_load_meter.ids.lb_info.text = f"Ambang Batas Beban yang diperbolehkan adalah {STANDARD_MAX_AXLE_LOAD} kg.\nBerat Roda Kendaraan Anda Dalam Range Ambang Batas"
                else:
                    screen_load_meter.ids.lb_info.text = f"Ambang Batas Beban yang diperbolehkan adalah {STANDARD_MAX_AXLE_LOAD} kg.\nBerat Roda Kendaraan Anda Diluar Ambang Batas"

                if(db_brake_total_value[dt_test_number] <= STANDARD_MAX_BRAKE):
                    screen_brake_meter.ids.lb_info.text = f"Ambang Batas Beban yang diperbolehkan adalah {STANDARD_MAX_AXLE_LOAD} kg.\nKekuatan Pengereman Kendaraan Anda Dalam Range Ambang Batas"
                else:
                    screen_brake_meter.ids.lb_info.text = f"Ambang Batas Beban yang diperbolehkan adalah {STANDARD_MAX_AXLE_LOAD} kg.\nKekuatan Pengereman Kendaraan Anda Diluar Ambang Batas"                

                if(db_handbrake_total_value[dt_test_number] <= STANDARD_MAX_BRAKE):
                    screen_handbrake_meter.ids.lb_info.text = f"Ambang Batas Beban yang diperbolehkan adalah {STANDARD_MAX_AXLE_LOAD} kg.\nKekuatan Pengereman Kendaraan Anda Dalam Range Ambang Batas"
                else:
                    screen_handbrake_meter.ids.lb_info.text = f"Ambang Batas Beban yang diperbolehkan adalah {STANDARD_MAX_AXLE_LOAD} kg.\nKekuatan Pengereman Kendaraan Anda Diluar Ambang Batas"                

            elif(count_starting > 0):
                if(flag_play):
                    screen_load_meter.ids.lb_test_subtitle.text = "MEMULAI PENGUKURAN"
                    screen_load_meter.ids.lb_load_l_val.text = str(count_starting)
                    screen_load_meter.ids.lb_load_r_val.text = " "
                    screen_load_meter.ids.lb_info.text = "Silahkan Tempatkan Kendaraan Anda Pada Tempat yang Sudah Disediakan"

                    screen_brake_meter.ids.lb_test_subtitle.text = "MEMULAI PENGUKURAN"
                    screen_brake_meter.ids.lb_brake_l_val.text = str(count_starting)
                    screen_brake_meter.ids.lb_brake_r_val.text = " "
                    screen_brake_meter.ids.lb_info.text = "Silahkan Tempatkan Kendaraan Anda Pada Tempat yang Sudah Disediakan"

                    screen_handbrake_meter.ids.lb_test_subtitle.text = "MEMULAI PENGUKURAN"
                    screen_handbrake_meter.ids.lb_handbrake_l_val.text = str(count_starting)
                    screen_handbrake_meter.ids.lb_handbrake_r_val.text = " "
                    screen_handbrake_meter.ids.lb_info.text = "Silahkan Tempatkan Kendaraan Anda Pada Tempat yang Sudah Disediakan"

            if(count_get_data <= 0):
                if(not flag_play):
                    screen_load_meter.ids.lb_test_result.md_bg_color = colors['Green']['200']
                    screen_load_meter.ids.lb_test_result.text_color = colors['Green']['700']
                    screen_load_meter.ids.lb_test_result.text = f"S{dt_test_number + 1}\nTOTAL {db_load_total_value[dt_test_number]}"
                    dt_load_flag = "Lulus"

                    screen_brake_meter.ids.lb_test_result.md_bg_color = colors['Green']['200']
                    screen_brake_meter.ids.lb_test_result.text_color = colors['Green']['700']
                    screen_brake_meter.ids.lb_test_result.text = f"S{dt_test_number + 1}\nTOTAL {db_brake_total_value[dt_test_number]}"
                    dt_brake_flag = "Lulus"

                    screen_handbrake_meter.ids.lb_test_result.md_bg_color = colors['Green']['200']
                    screen_handbrake_meter.ids.lb_test_result.text_color = colors['Green']['700']
                    screen_handbrake_meter.ids.lb_test_result.text = f"S{dt_test_number + 1}\nTOTAL {db_handbrake_total_value[dt_test_number]}"
                    dt_handbrake_flag = "Lulus"

            elif(count_get_data > 0):
                screen_load_meter.ids.lb_test_result.md_bg_color = "#EEEEEE"
                screen_load_meter.ids.lb_test_result.text = ""

                screen_brake_meter.ids.lb_test_result.md_bg_color = "#EEEEEE"
                screen_brake_meter.ids.lb_test_result.text = ""
                
                screen_handbrake_meter.ids.lb_test_result.md_bg_color = "#EEEEEE"
                screen_handbrake_meter.ids.lb_test_result.text = ""
            
            for i in range(10):
                screen_resume.ids[f'lb_axle_number{i}'].text = '' if (db_load_total_value[i] + db_brake_total_value[i] + db_handbrake_total_value[i] == 0) else f'Sumbu {i+1}'
                screen_resume.ids[f'lb_load_total{i}'].text = str(db_load_total_value[i]) if db_load_total_value[i] > 0.0 else ''
                screen_resume.ids[f'lb_brake_total{i}'].text = str(db_brake_total_value[i]) if db_brake_total_value[i] > 0.0 else ''
                # screen_resume.ids[f'lb_brake_efficiency{i}'].text = str(db_brake_efficiency_value[dt_test_number])
                # screen_resume.ids[f'lb_brake_difference{i}'].text = str(db_brake_difference_value[dt_test_number])
                screen_resume.ids[f'lb_handbrake_total{i}'].text = str(db_handbrake_total_value[i]) if db_handbrake_total_value[i] > 0.0 else ''
                # screen_resume.ids[f'lb_handbrake_efficiency{i}'].text = str(db_handbrake_efficiency_value[dt_test_number])
                # screen_resume.ids[f'lb_handbrake_difference{i}'].text = str(db_handbrake_difference_value[dt_test_number])

                if(dt_test_number == i):
                    screen_menu.ids[f'bt_S{i}'].md_bg_color = colors['Red']['A200']
                else:
                    screen_menu.ids[f'bt_S{i}'].md_bg_color = colors['Green']['200']

            screen_resume.ids.lb_load_total_sum.text = str(dt_load_total_value)
            screen_resume.ids.lb_brake_total_sum.text = str(dt_brake_total_value)
            screen_resume.ids.lb_brake_efficiency_sum.text = str(dt_brake_efficiency_value)
            screen_resume.ids.lb_brake_difference_sum.text = str(dt_brake_difference_value)
            screen_resume.ids.lb_handbrake_total_sum.text = str(dt_handbrake_total_value)
            screen_resume.ids.lb_handbrake_efficiency_sum.text = str(dt_handbrake_efficiency_value)
            screen_resume.ids.lb_handbrake_difference_sum.text = str(dt_handbrake_difference_value)

            self.ids.bt_logout.disabled = False if dt_user != '' else True
            
            self.ids.lb_operator.text = f'Login Sebagai: {dt_user}' if dt_user != '' else 'Silahkan Login'
            screen_home.ids.lb_operator.text = f'Login Sebagai: {dt_user}' if dt_user != '' else 'Silahkan Login'
            screen_login.ids.lb_operator.text = f'Login Sebagai: {dt_user}' if dt_user != '' else 'Silahkan Login'
            screen_load_meter.ids.lb_operator.text = f'Login Sebagai: {dt_user}' if dt_user != '' else 'Silahkan Login'
            screen_brake_meter.ids.lb_operator.text = f'Login Sebagai: {dt_user}' if dt_user != '' else 'Silahkan Login'
            screen_handbrake_meter.ids.lb_operator.text = f'Login Sebagai: {dt_user}' if dt_user != '' else 'Silahkan Login'

        except Exception as e:
            toast_msg = f'Error Update Display: {e}'
            toast(toast_msg)       

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

    def regular_get_data(self, dt):
        global flag_play
        global dt_no_antrian
        global count_starting, count_get_data
        global mydb
        global db_load_left_value, db_load_right_value, db_load_total_value
        global db_brake_left_value, db_brake_right_value, db_brake_total_value, db_brake_efficiency_value, db_brake_difference_value
        global db_handbrake_left_value, db_handbrake_right_value, db_handbrake_total_value, db_handbrake_efficiency_value, db_handbrake_difference_value
        global dt_load_total_value, dt_brake_total_value, dt_brake_efficiency_value, dt_brake_difference_value, dt_handbrake_total_value, dt_handbrake_efficiency_value, dt_handbrake_difference_value
        global dt_test_number

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
                axle_load_registers = MODBUS_CLIENT.read_holding_registers(REGISTER_DATA_LOAD, count=2, slave=1) #V1200 - V1201
                brake_registers = MODBUS_CLIENT.read_holding_registers(REGISTER_DATA_BRAKE, count=2, slave=1) #V1250 - V1201
                MODBUS_CLIENT.close()

                if self.screen_manager.current == 'screen_load_meter':
                    db_load_left_value[dt_test_number] = np.round(axle_load_registers.registers[0] / 10 , 2)
                    db_load_right_value[dt_test_number] = np.round(axle_load_registers.registers[1] / 10 , 2) 
                    if(dt_test_number == 0 and db_load_right_value[dt_test_number] >= 60):
                        db_load_right_value[dt_test_number] = db_load_right_value[dt_test_number] - 60
                    db_load_total_value[dt_test_number] = db_load_left_value[dt_test_number] + db_load_right_value[dt_test_number]
                    dt_load_total_value = np.round(np.sum(db_load_total_value) ,2)

                if self.screen_manager.current == 'screen_brake_meter':               
                    db_brake_left_value[dt_test_number] = np.round(brake_registers.registers[0] / 10 , 2) - db_load_left_value[dt_test_number]
                    db_brake_right_value[dt_test_number] = np.round(brake_registers.registers[1] / 10 , 2) - db_load_right_value[dt_test_number]
                    db_brake_total_value[dt_test_number] = db_brake_left_value[dt_test_number] + db_brake_right_value[dt_test_number]
                    db_brake_efficiency_value[dt_test_number] = ((db_brake_total_value[dt_test_number] - db_load_total_value[dt_test_number]) / db_load_total_value[dt_test_number]) * 100
                    db_brake_difference_value[dt_test_number] = (np.abs(db_brake_total_value[dt_test_number] - db_brake_total_value[dt_test_number]) / db_load_total_value[dt_test_number]) * 100
                    dt_brake_total_value = np.round(np.sum(db_brake_total_value), 2)
                    dt_brake_efficiency_value = np.round((dt_brake_total_value / dt_load_total_value) * 100, 2)
                    dt_brake_difference_value = np.round(np.sum(db_brake_difference_value), 2)

                if self.screen_manager.current == 'screen_handbrake_meter':                      
                    db_handbrake_left_value[dt_test_number] = np.round(brake_registers.registers[0] / 10 , 2) - db_load_left_value[dt_test_number] 
                    db_handbrake_right_value[dt_test_number] = np.round(brake_registers.registers[1] / 10 , 2) - db_load_right_value[dt_test_number] 
                    db_handbrake_total_value[dt_test_number] = db_handbrake_left_value[dt_test_number] + db_handbrake_right_value[dt_test_number]
                    db_handbrake_efficiency_value[dt_test_number] = ((db_handbrake_total_value[dt_test_number] - db_load_total_value[dt_test_number]) / db_load_total_value[dt_test_number]) * 100
                    db_handbrake_difference_value[dt_test_number] = (np.abs(db_handbrake_total_value[dt_test_number] - db_handbrake_total_value[dt_test_number]) / db_load_total_value[dt_test_number]) * 100
                    dt_handbrake_total_value = np.round(np.sum(db_handbrake_total_value), 2)
                    dt_handbrake_efficiency_value = np.round((dt_handbrake_total_value / dt_load_total_value) * 100, 2)
                    dt_handbrake_difference_value = np.round(np.sum(db_handbrake_difference_value), 2)

        except Exception as e:
            toast_msg = f'Error Get Data: {e}'
            print(toast_msg)      

    def exec_reload_database(self):
        global mydb
        try:
            mydb = mysql.connector.connect(host = DB_HOST,user = DB_USER,password = DB_PASSWORD,database = DB_NAME)
        except Exception as e:
            toast_msg = f'Error Initiate Database: {e}'
            toast(toast_msg)   

    def exec_reload_table(self):
        global mydb, db_antrian, db_merk
        global dt_dash_pendaftaran, dt_dash_belum_uji, dt_dash_sudah_uji

        try:
            tb_antrian = mydb.cursor()
            tb_antrian.execute(f"SELECT noantrian, nopol, nouji, load_flag, brake_flag, handbrake_flag, user, merk, type, idjeniskendaraan, jbb, bahan_bakar, warna FROM {TB_DATA}")
            result_tb_antrian = tb_antrian.fetchall()
            mydb.commit()
            db_antrian = np.array(result_tb_antrian).T
            db_pendaftaran = np.array(result_tb_antrian)
            dt_dash_pendaftaran = db_pendaftaran[:,3].size
            dt_dash_belum_uji = np.where(db_pendaftaran[:,3] == 0)[0].size
            dt_dash_sudah_uji = np.where(db_pendaftaran[:,3] == 1)[0].size

            tb_merk = mydb.cursor()
            tb_merk.execute(f"SELECT ID, DESCRIPTION FROM {TB_MERK}")
            result_tb_merk = tb_merk.fetchall()
            mydb.commit()
            db_merk = np.array(result_tb_merk)

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
                        MDLabel(text=f"{db_antrian[0, i]}", size_hint_x= 0.05),
                        MDLabel(text=f"{db_antrian[1, i]}", size_hint_x= 0.08),
                        MDLabel(text=f"{db_antrian[2, i]}", size_hint_x= 0.08),
                        MDLabel(text='Belum Tes' if (int(db_antrian[3, i]) == 0) else 'Sudah Tes', size_hint_x= 0.07),
                        MDLabel(text='Belum Tes' if (int(db_antrian[4, i]) == 0) else 'Sudah Tes', size_hint_x= 0.07),
                        MDLabel(text='Belum Tes' if (int(db_antrian[5, i]) == 0) else 'Sudah Tes', size_hint_x= 0.07),
                        MDLabel(text=f"{db_antrian[6, i]}", size_hint_x= 0.08),
                        MDLabel(text=f"{db_merk[np.where(db_merk == db_antrian[7, i])[0][0],1]}", size_hint_x= 0.08),
                        MDLabel(text=f"{db_antrian[8, i]}", size_hint_x= 0.05),
                        MDLabel(text=f"{db_antrian[9, i]}", size_hint_x= 0.13),
                        MDLabel(text=f"{db_antrian[10, i]}", size_hint_x= 0.05),
                        MDLabel(text=f"{db_antrian[11, i]}", size_hint_x= 0.08),
                        MDLabel(text=f"{db_antrian[12, i]}", size_hint_x= 0.08),

                        ripple_behavior = True,
                        on_press = self.on_antrian_row_press,
                        padding = 20,
                        id=f"card_antrian{i}",
                        size_hint_y=None,
                        height="60dp",
                        )
                    )

        except Exception as e:
            toast_msg = f'Error Reload Table: {e}'
            print(toast_msg)

    def exec_start(self):
        global dt_load_flag, dt_brake_flag, dt_handbrake_flag, dt_no_antrian, dt_user
        global flag_play
        if (dt_user != ''):
            if (dt_load_flag == 'Belum Tes' or dt_brake_flag == 'Belum Tes' or dt_handbrake_flag == 'Belum Tes'):
                self.open_screen_menu()
            else:
                toast(f'No. Antrian {dt_no_antrian} Sudah Tes')
        else:
            toast(f'Silahkan Login Untuk Melakukan Pengujian')        

    def open_screen_menu(self):
        self.screen_manager.current = 'screen_menu'

    def exec_logout(self):
        global dt_user

        dt_user = ""
        self.screen_manager.current = 'screen_login'

    def exec_navigate_home(self):
        try:
            self.screen_manager.current = 'screen_home'

        except Exception as e:
            toast_msg = f'Error Navigate to Home Screen: {e}'
            toast(toast_msg)        

    def exec_navigate_login(self):
        global dt_user
        try:
            if (dt_user == ""):
                self.screen_manager.current = 'screen_login'
            else:
                toast(f"Anda sudah login sebagai {dt_user}")

        except Exception as e:
            toast_msg = f'Error Navigate to Login Screen: {e}'
            toast(toast_msg)    

    def exec_navigate_main(self):
        try:
            self.screen_manager.current = 'screen_main'

        except Exception as e:
            toast_msg = f'Error Navigate to Main Screen: {e}'
            toast(toast_msg)   

class ScreenMenu(MDScreen):        
    def __init__(self, **kwargs):
        super(ScreenMenu, self).__init__(**kwargs)
        Clock.schedule_once(self.delayed_init, 2)        

    def delayed_init(self, dt):
        pass

    def exec_select_axle(self, number):
        global dt_test_number

        dt_test_number = number - 1

    def exec_start_load(self):
        global flag_play
        global count_starting, count_get_data

        screen_main = self.screen_manager.get_screen('screen_main')

        count_starting = COUNT_STARTING
        count_get_data = COUNT_ACQUISITION

        if(not flag_play):
            Clock.schedule_interval(screen_main.regular_get_data, GET_DATA_INTERVAL)
            self.open_screen_load_meter()
            flag_play = True

    def exec_start_brake(self):
        global flag_play
        global count_starting, count_get_data

        screen_main = self.screen_manager.get_screen('screen_main')

        count_starting = COUNT_STARTING
        count_get_data = COUNT_ACQUISITION

        if(not flag_play):
            Clock.schedule_interval(screen_main.regular_get_data, GET_DATA_INTERVAL)
            self.open_screen_brake_meter()
            flag_play = True

    def exec_start_handbrake(self):
        global flag_play
        global count_starting, count_get_data

        screen_main = self.screen_manager.get_screen('screen_main')

        count_starting = COUNT_STARTING
        count_get_data = COUNT_ACQUISITION

        if(not flag_play):
            Clock.schedule_interval(screen_main.regular_get_data, GET_DATA_INTERVAL)
            self.open_screen_handbrake_meter()
            flag_play = True

    def exec_navigate_main(self):
        try:
            self.screen_manager.current = 'screen_main'

        except Exception as e:
            toast_msg = f'Error Navigate to Main Screen: {e}'
            toast(toast_msg)   

    def open_screen_load_meter(self):
        self.screen_manager.current = 'screen_load_meter'

    def open_screen_brake_meter(self):
        self.screen_manager.current = 'screen_brake_meter'

    def open_screen_handbrake_meter(self):
        self.screen_manager.current = 'screen_handbrake_meter'

    def exec_navigate_resume(self):
        self.screen_manager.current = 'screen_resume'

class ScreenLoadMeter(MDScreen):        
    def __init__(self, **kwargs):
        super(ScreenLoadMeter, self).__init__(**kwargs)
        Clock.schedule_once(self.delayed_init, 2)        

    def delayed_init(self, dt):
        pass

    def exec_reload(self):
        global flag_play
        global count_starting, count_get_data, db_load_left_value, db_load_right_value
        global dt_test_number

        screen_main = self.screen_manager.get_screen('screen_main')

        count_starting = COUNT_STARTING
        count_get_data = COUNT_ACQUISITION
        db_load_left_value[dt_test_number] = 0
        db_load_right_value[dt_test_number] = 0
        self.ids.bt_reload.disabled = True
        self.ids.lb_load_l_val.text = "..."
        self.ids.lb_load_r_val.text = " "

        if(not flag_play):
            Clock.schedule_interval(screen_main.regular_get_data, GET_DATA_INTERVAL)
            flag_play = True

    def exec_navigate_back(self):
        global flag_play        
        global count_starting, count_get_data

        count_starting = COUNT_STARTING
        count_get_data = COUNT_ACQUISITION
        flag_play = False   
        self.screen_manager.current = 'screen_menu'

class ScreenBrakeMeter(MDScreen):        
    def __init__(self, **kwargs):
        super(ScreenBrakeMeter, self).__init__(**kwargs)
        Clock.schedule_once(self.delayed_init, 2)
        
    def delayed_init(self, dt):
        pass

    def exec_cylinder_up(self):
        global flag_conn_stat
        global flag_cylinder

        if(not flag_cylinder):
            flag_cylinder = True

        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_coil(3082, flag_cylinder, slave=1) #M10
                MODBUS_CLIENT.close()
        except:
            toast("error send exec_cylinder_up data to PLC Slave") 

    def exec_cylinder_down(self):
        global flag_conn_stat
        global flag_cylinder

        if(flag_cylinder):
            flag_cylinder = False

        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_coil(3083, not flag_cylinder, slave=1) #M11
                MODBUS_CLIENT.close()
        except:
            toast("error send exec_cylinder_down data to PLC Slave") 

    def exec_cylinder_stop(self):
        global flag_conn_stat

        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_coil(3082, False, slave=1) #M10
                MODBUS_CLIENT.write_coil(3083, False, slave=1) #M11
                MODBUS_CLIENT.close()
        except:
            toast("error send exec_cylinder_stop data to PLC Slave")   

    def exec_reload(self):
        global flag_play
        global count_starting, count_get_data, db_brake_left_value, db_brake_right_value
        global dt_test_number

        screen_main = self.screen_manager.get_screen('screen_main')

        count_starting = COUNT_STARTING
        count_get_data = COUNT_ACQUISITION
        db_brake_left_value[dt_test_number] = 0
        db_brake_right_value[dt_test_number] = 0
        self.ids.bt_reload.disabled = True
        self.ids.lb_brake_l_val.text = "..."
        self.ids.lb_brake_r_val.text = " "

        if(not flag_play):
            Clock.schedule_interval(screen_main.regular_get_data, GET_DATA_INTERVAL)
            flag_play = True

    def exec_navigate_back(self):
        global flag_play        
        global count_starting, count_get_data

        count_starting = COUNT_STARTING
        count_get_data = COUNT_ACQUISITION
        flag_play = False   
        self.screen_manager.current = 'screen_menu'

class ScreenHandbrakeMeter(MDScreen):        
    def __init__(self, **kwargs):
        super(ScreenHandbrakeMeter, self).__init__(**kwargs)
        Clock.schedule_once(self.delayed_init, 2)
        
    def delayed_init(self, dt):
        pass

    def exec_cylinder_up(self):
        global flag_conn_stat
        global flag_cylinder

        if(not flag_cylinder):
            flag_cylinder = True

        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_coil(3082, flag_cylinder, slave=1) #M10
                MODBUS_CLIENT.close()
        except:
            toast("error send exec_cylinder_up data to PLC Slave") 

    def exec_cylinder_down(self):
        global flag_conn_stat
        global flag_cylinder

        if(flag_cylinder):
            flag_cylinder = False

        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_coil(3083, not flag_cylinder, slave=1) #M11
                MODBUS_CLIENT.close()
        except:
            toast("error send exec_cylinder_down data to PLC Slave") 

    def exec_cylinder_stop(self):
        global flag_conn_stat

        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_coil(3082, False, slave=1) #M10
                MODBUS_CLIENT.write_coil(3083, False, slave=1) #M11
                MODBUS_CLIENT.close()
        except:
            toast("error send exec_cylinder_stop data to PLC Slave")   

    def exec_reload(self):
        global flag_play
        global count_starting, count_get_data, db_handbrake_left_value, db_handbrake_right_value
        global dt_test_number

        screen_main = self.screen_manager.get_screen('screen_main')

        count_starting = COUNT_STARTING
        count_get_data = COUNT_ACQUISITION
        db_handbrake_left_value[dt_test_number] = 0
        db_handbrake_right_value[dt_test_number] = 0
        self.ids.bt_reload.disabled = True
        self.ids.lb_brake_l_val.text = "..."
        self.ids.lb_brake_r_val.text = " "

        if(not flag_play):
            Clock.schedule_interval(screen_main.regular_get_data, GET_DATA_INTERVAL)
            flag_play = True

    def exec_navigate_back(self):
        global flag_play        
        global count_starting, count_get_data

        count_starting = COUNT_STARTING
        count_get_data = COUNT_ACQUISITION
        flag_play = False   
        self.screen_manager.current = 'screen_menu'

class ScreenResume(MDScreen):        
    def __init__(self, **kwargs):
        super(ScreenResume, self).__init__(**kwargs)
        Clock.schedule_once(self.delayed_init, 2)        

    def delayed_init(self, dt):
        pass


    def exec_navigate_back(self):
        try:
            self.screen_manager.current = 'screen_menu'

        except Exception as e:
            toast_msg = f'Error Navigate to Menu Screen: {e}'
            toast(toast_msg)   

    def exec_save(self):
        global flag_play
        global count_starting, count_get_data
        global mydb, db_antrian
        global db_load_left_value, db_load_right_value, db_load_total_value
        global db_brake_left_value, db_brake_right_value, db_brake_total_value, db_brake_efficiency_value, db_brake_difference_value
        global db_handbrake_left_value, db_handbrake_right_value, db_handbrake_total_value, db_handbrake_efficiency_value, db_handbrake_difference_value
        global dt_load_total_value, dt_brake_total_value, dt_brake_efficiency_value, dt_brake_difference_value, dt_handbrake_total_value, dt_handbrake_efficiency_value, dt_handbrake_difference_value
        global dt_test_number

        try:
            self.ids.bt_save.disabled = True

            mycursor = mydb.cursor()
            sql = f"UPDATE {TB_DATA} SET load_flag = %s, load_l_value = %s, load_r_value = %s, load_total_value = %s, load_user = %s, load_post = %s WHERE noantrian = %s"
            sql_load_flag = (1 if dt_load_flag == "Lulus" else 2)
            dt_load_post = str(time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()))
            sql_val = (sql_load_flag, np.average(db_load_left_value), np.average(db_load_right_value), dt_load_total_value, dt_load_user, dt_load_post, dt_no_antrian)
            mycursor.execute(sql, sql_val)
            mydb.commit()

            mycursor = mydb.cursor()
            sql = f"UPDATE {TB_DATA} SET brake_flag = %s, brake_l_value = %s, brake_r_value = %s, brake_total_value = %s, brake_efficiency_value = %s, brake_difference_value = %s, load_user = %s, load_post = %s WHERE noantrian = %s"
            sql_load_flag = (1 if dt_load_flag == "Lulus" else 2)
            dt_load_post = str(time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()))
            sql_val = (sql_load_flag, np.average(db_load_left_value), np.average(db_load_right_value), dt_load_total_value, dt_load_user, dt_load_post, dt_no_antrian)
            mycursor.execute(sql, sql_val)
            mydb.commit()

            mycursor = mydb.cursor()
            sql = f"UPDATE {TB_DATA} SET handbrake_flag = %s, handbrake_l_value = %s, handbrake_r_value = %s, handbrake_total_value = %s, handbrake_efficiency_value = %s, handbrake_difference_value = %s, load_user = %s, load_post = %s WHERE noantrian = %s"
            sql_load_flag = (1 if dt_load_flag == "Lulus" else 2)
            dt_load_post = str(time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()))
            sql_val = (sql_load_flag, np.average(db_load_left_value), np.average(db_load_right_value), dt_load_total_value, dt_load_user, dt_load_post, dt_no_antrian)
            mycursor.execute(sql, sql_val)
            mydb.commit()

            self.exec_navigate_main()
        
        except Exception as e:
            toast_msg = f'Error Save Data: {e}'
            toast(toast_msg)

    def exec_navigate_main(self):
        try:
            self.screen_manager.current = 'screen_main'

        except Exception as e:
            toast_msg = f'Error Navigate to Main Screen: {e}'
            toast(toast_msg)  

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
        self.icon = 'assets/images/logo-load-app.png'

        LabelBase.register(
            name="Orbitron-Regular",
            fn_regular="assets/fonts/Orbitron-Regular.ttf")
        
        LabelBase.register(
            name="Draco",
            fn_regular="assets/fonts/Draco.otf")        

        LabelBase.register(
            name="Recharge",
            fn_regular="assets/fonts/Recharge.otf") 
        
        theme_font_styles.append('Display')
        self.theme_cls.font_styles["Display"] = [
            "Orbitron-Regular", 72, False, 0.15]       

        theme_font_styles.append('H4')
        self.theme_cls.font_styles["H4"] = [
            "Recharge", 30, False, 0.15] 

        theme_font_styles.append('H5')
        self.theme_cls.font_styles["H5"] = [
            "Recharge", 20, False, 0.15] 

        theme_font_styles.append('H6')
        self.theme_cls.font_styles["H6"] = [
            "Recharge", 16, False, 0.15] 

        theme_font_styles.append('Subtitle1')
        self.theme_cls.font_styles["Subtitle1"] = [
            "Recharge", 12, False, 0.15] 

        theme_font_styles.append('Body1')
        self.theme_cls.font_styles["Body1"] = [
            "Recharge", 12, False, 0.15] 
        
        theme_font_styles.append('Button')
        self.theme_cls.font_styles["Button"] = [
            "Recharge", 10, False, 0.15] 

        theme_font_styles.append('Caption')
        self.theme_cls.font_styles["Caption"] = [
            "Recharge", 8, False, 0.15]              
        
        Window.fullscreen = 'auto'
        Builder.load_file('main.kv')
        return RootScreen()

if __name__ == '__main__':
    LoadBrakeMeterApp().run()
