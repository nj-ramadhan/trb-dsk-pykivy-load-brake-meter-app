import datetime
import os, sys, time

if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
    running_mode = 'Frozen/executable'
else:
    try:
        app_full_path = os.path.realpath(__file__)
        application_path = os.path.dirname(app_full_path)
        running_mode = "Non-interactive"
    except NameError:
        application_path = os.getcwd()
        running_mode = 'Interactive'

logger_name = f'app.log'
logger_dir = os.path.join(application_path, "logs")

from kivy.config import Config
Config.set('kivy', 'keyboard_mode', 'system')

from kivy.logger import Logger
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.uix.screenmanager import ScreenManager
from kivymd.font_definitions import theme_font_styles
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.textfield import MDTextField
from kivymd.uix.menu import MDDropdownMenu
from kivy.metrics import dp
from kivymd.toast import toast
from kivymd.app import MDApp
import numpy as np
import configparser, hashlib, mysql.connector
from pymodbus.client import ModbusTcpClient
from fpdf import FPDF
from escpos.printer import Serial

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
config_full_path = os.path.join(application_path, config_name)
config = configparser.ConfigParser()
config.read(config_full_path)

## App Setting
APP_TITLE = config['app']['APP_TITLE']
APP_SUBTITLE = config['app']['APP_SUBTITLE']
IMG_LOGO_PEMKAB = config['app']['IMG_LOGO_PEMKAB']
IMG_LOGO_DISHUB = config['app']['IMG_LOGO_DISHUB']
LB_PEMKAB = config['app']['LB_PEMKAB']
LB_DISHUB = config['app']['LB_DISHUB']
LB_UNIT = config['app']['LB_UNIT']
LB_UNIT_ADDRESS = config['app']['LB_UNIT_ADDRESS']

# SQL setting
DB_HOST = "194.31.53.37"
DB_USER = "Pndujikir2022!"
DB_PASSWORD = "@Kirpnd2022!"

DB_NAME = "pkbpandeglang"
TB_DATA = "tb_cekident"
TB_USER = "users"
TB_MERK = "merk"
TB_BAHAN_BAKAR = "bahanbakar"
TB_WARNA = "warna"
TB_DATA_MASTER = "identkendaraan"

FTP_HOST = "194.31.53.37"
FTP_USER = "root"
FTP_PASS = "@D15HUBp2022!"

# system setting
TIME_OUT = int(config['setting']['TIME_OUT'])
COUNT_STARTING = int(config['setting']['COUNT_STARTING'])
COUNT_ACQUISITION = int(config['setting']['COUNT_ACQUISITION'])
UPDATE_CAROUSEL_INTERVAL = float(config['setting']['UPDATE_CAROUSEL_INTERVAL'])
UPDATE_CONNECTION_INTERVAL = float(config['setting']['UPDATE_CONNECTION_INTERVAL'])
GET_DATA_INTERVAL = float(config['setting']['GET_DATA_INTERVAL'])

PRINTER_THERM_COM = str(config['setting']['PRINTER_THERM_COM'])
PRINTER_THERM_BAUD = int(config['setting']['PRINTER_THERM_BAUD'])
PRINTER_THERM_BYTESIZE = int(config['setting']['PRINTER_THERM_BYTESIZE'])
PRINTER_THERM_PARITY = str(config['setting']['PRINTER_THERM_PARITY'])
PRINTER_THERM_STOPBITS = int(config['setting']['PRINTER_THERM_STOPBITS'])
PRINTER_THERM_TIMEOUT = float(config['setting']['PRINTER_THERM_TIMEOUT'])
PRINTER_THERM_DSRDTR = bool(config['setting']['PRINTER_THERM_DSRDTR'])

MODBUS_IP_PLC = config['setting']['MODBUS_IP_PLC']
MODBUS_CLIENT = ModbusTcpClient(MODBUS_IP_PLC)
REGISTER_DATA_LOAD_L = int(config['setting']['REGISTER_DATA_LOAD_L']) # 1912 = V1400
REGISTER_DATA_LOAD_R = int(config['setting']['REGISTER_DATA_LOAD_R']) # 1922 = V1410
REGISTER_DATA_BRAKE_L = int(config['setting']['REGISTER_DATA_BRAKE_L']) # 1932 = V1420
REGISTER_DATA_BRAKE_R = int(config['setting']['REGISTER_DATA_BRAKE_R']) # 1942 = V1430
MAX_LOAD_DATA = int(config['setting']['MAX_LOAD_DATA'])
MAX_BRAKE_DATA = int(config['setting']['MAX_BRAKE_DATA'])

# system standard
STANDARD_MAX_AXLE_LOAD = float(config['standard']['STANDARD_MAX_AXLE_LOAD']) # in kg
STANDARD_MAX_DIFFERENCE_AXLE_LOAD = float(config['standard']['STANDARD_MAX_DIFFERENCE_AXLE_LOAD']) # %
STANDARD_MAX_BRAKE = float(config['standard']['STANDARD_MAX_BRAKE']) # kg
STANDARD_MAX_HANDBRAKE = float(config['standard']['STANDARD_MAX_HANDBRAKE']) # kg
STANDARD_MAX_DIFFERENCE_BRAKE = float(config['standard']['STANDARD_MAX_DIFFERENCE_BRAKE']) # %
STANDARD_MIN_EFFICIENCY_BRAKE = float(config['standard']['STANDARD_MIN_EFFICIENCY_BRAKE']) # %
STANDARD_MAX_DIFFERENCE_HANDBRAKE = float(config['standard']['STANDARD_MAX_DIFFERENCE_HANDBRAKE']) # %
STANDARD_MIN_EFFICIENCY_HANDBRAKE = float(config['standard']['STANDARD_MIN_EFFICIENCY_HANDBRAKE']) # %

class ScreenHome(MDScreen):
    def __init__(self, **kwargs):
        super(ScreenHome, self).__init__(**kwargs)
        Clock.schedule_once(self.delayed_init, 1)
    
    def delayed_init(self, dt):
        self.ids.lb_title.text = APP_TITLE
        self.ids.lb_subtitle.text = APP_SUBTITLE
        self.ids.img_pemkab.source = f'assets/images/{IMG_LOGO_PEMKAB}'
        self.ids.img_dishub.source = f'assets/images/{IMG_LOGO_DISHUB}'
        self.ids.lb_pemkab.text = LB_PEMKAB
        self.ids.lb_dishub.text = LB_DISHUB
        self.ids.lb_unit.text = LB_UNIT
        self.ids.lb_unit_address.text = LB_UNIT_ADDRESS

    def on_enter(self):
        Clock.schedule_interval(self.regular_update_carousel, 3)

    def on_leave(self):
        Clock.unschedule(self.regular_update_carousel)

    def regular_update_carousel(self, dt):
        try:
            self.ids.carousel.index += 1
            
        except Exception as e:
            toast_msg = f'Gagal Memperbaharui Tampilan Carousel'
            toast(toast_msg)                
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_navigate_home(self):
        try:
            self.screen_manager.current = 'screen_home'

        except Exception as e:
            toast_msg = f'Terjadi kesalahan saat berpindah ke halaman Beranda'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")

    def exec_navigate_login(self):
        global dt_user
        try:
            if (dt_user == ""):
                self.screen_manager.current = 'screen_login'
            else:
                toast_msg = f"Anda sudah login sebagai {dt_user}"
                toast(toast_msg)
                Logger.info(f"{self.name}: {toast_msg}")  

        except Exception as e:
            toast_msg = f'Terjadi kesalahan saat berpindah ke halaman Login'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_navigate_main(self):
        try:
            self.screen_manager.current = 'screen_main'

        except Exception as e:
            toast_msg = f'Terjadi kesalahan saat berpindah ke halaman Utama'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

class ScreenLogin(MDScreen):
    def __init__(self, **kwargs):
        super(ScreenLogin, self).__init__(**kwargs)
        Clock.schedule_once(self.delayed_init, 1)
    
    def delayed_init(self, dt):
        self.ids.lb_title.text = APP_TITLE
        self.ids.lb_subtitle.text = APP_SUBTITLE        
        self.ids.img_pemkab.source = f'assets/images/{IMG_LOGO_PEMKAB}'
        self.ids.img_dishub.source = f'assets/images/{IMG_LOGO_DISHUB}'
        self.ids.lb_pemkab.text = LB_PEMKAB
        self.ids.lb_dishub.text = LB_DISHUB
        self.ids.lb_unit.text = LB_UNIT
        self.ids.lb_unit_address.text = LB_UNIT_ADDRESS

    def exec_cancel(self):
        try:
            self.ids.tx_username.text = ""
            self.ids.tx_password.text = ""    

        except Exception as e:
            toast_msg = f'error Login: {e}'
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_login(self):
        global mydb, db_users
        global dt_id_user, dt_user, dt_foto_user

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
            mycursor.execute(f"SELECT id_user, nama, username, password, image FROM {TB_USER} WHERE username = '{input_username}' and password = '{hashed_password.hexdigest()}'")
            myresult = mycursor.fetchone()
            db_users = np.array(myresult).T
            
            if myresult is None:
                toast_msg = f'Gagal Masuk, Nama Pengguna atau Password Salah'
                toast(toast_msg) 
                Logger.warning(f"{self.name}: {toast_msg}") 
            else:
                toast_msg = f'Berhasil Masuk, Selamat Datang {myresult[1]}'
                toast(toast_msg)
                Logger.info(f"{self.name}: {toast_msg}")  

                dt_id_user = myresult[0]
                dt_user = myresult[1]
                dt_foto_user = myresult[4]
                self.ids.tx_username.text = ""
                self.ids.tx_password.text = "" 
                self.screen_manager.current = 'screen_main'

        except Exception as e:
            toast_msg = f'Gagal masuk, silahkan isi nama user dan password yang sesuai'
            toast(toast_msg)  
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_navigate_home(self):
        try:
            self.screen_manager.current = 'screen_home'

        except Exception as e:
            toast_msg = f'Gagal Berpindah ke Halaman Awal'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")

    def exec_navigate_login(self):
        global dt_user
        try:
            if (dt_user == ""):
                self.screen_manager.current = 'screen_login'
            else:
                toast_msg = f"Anda sudah login sebagai {dt_user}"
                toast(toast_msg)
                Logger.info(f"{self.name}: {toast_msg}")  

        except Exception as e:
            toast_msg = f'Gagal Berpindah ke Halaman Login'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_navigate_main(self):
        try:
            self.screen_manager.current = 'screen_main'

        except Exception as e:
            toast_msg = f'Gagal Berpindah ke Halaman Utama'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

class ScreenMain(MDScreen):   
    def __init__(self, **kwargs):
        super(ScreenMain, self).__init__(**kwargs)
        global flag_conn_stat, flag_play, flag_motor_brake
        global count_starting, count_get_data
        global dt_user, dt_foto_user, dt_no_antri, dt_no_pol, dt_no_uji, dt_sts_uji, dt_nama
        global dt_merk, dt_type, dt_jns_kend, dt_jbb, dt_brt_ksg, dt_warna, dt_chasis, dt_no_mesin    
        global dt_id_user    
        global db_load_left_value, db_load_right_value, db_load_total_value, db_load_flag
        global dt_load_total_value, dt_load_flag, dt_id_user
        global db_brake_left_value, db_brake_right_value, db_brake_total_value, db_brake_difference_value, db_brake_flag
        global dt_brake_total_value, dt_brake_efficiency_value, dt_brake_difference_value, dt_brake_flag
        global db_handbrake_left_value, db_handbrake_right_value, db_handbrake_total_value, db_handbrake_difference_value, db_handbrake_flag
        global dt_handbrake_total_value, dt_handbrake_efficiency_value, dt_handbrake_difference_value, dt_handbrake_flag
        global dt_test_number, dt_dash_antri, dt_dash_belum_uji, dt_dash_sudah_uji

        count_starting = COUNT_STARTING
        count_get_data = COUNT_ACQUISITION

        flag_conn_stat = flag_play = flag_motor_brake = False
        dt_user = dt_foto_user = dt_no_antri = dt_no_pol = dt_no_uji = dt_sts_uji = dt_nama = ""
        dt_merk = dt_type = dt_jns_kend = dt_jbb = dt_brt_ksg = dt_warna = dt_chasis = dt_no_mesin = ""
        dt_id_user = 1
        dt_test_number = 0
        dt_dash_antri = dt_dash_belum_uji = dt_dash_sudah_uji = 0

        db_load_left_value = np.zeros(12, dtype=float)
        db_load_right_value = np.zeros(12, dtype=float)
        db_load_total_value = np.zeros(12, dtype=float)
        db_load_flag = np.zeros(12, dtype=int)
        dt_load_total_value = dt_load_flag = 0

        db_brake_left_value = np.zeros(12, dtype=float)
        db_brake_right_value = np.zeros(12, dtype=float)
        db_brake_total_value = np.zeros(12, dtype=float)
        db_brake_difference_value = np.zeros(12, dtype=float)
        db_brake_flag = np.zeros(12, dtype=int)
        dt_brake_total_value = dt_brake_efficiency_value = dt_brake_difference_value = dt_brake_flag = 0

        db_handbrake_left_value = np.zeros(12, dtype=float)
        db_handbrake_right_value = np.zeros(12, dtype=float)
        db_handbrake_total_value = np.zeros(12, dtype=float)
        db_handbrake_difference_value = np.zeros(12, dtype=float)
        db_handbrake_flag = np.zeros(12, dtype=int)
        dt_handbrake_total_value = dt_handbrake_efficiency_value = dt_handbrake_difference_value = dt_handbrake_flag = 0

        Clock.schedule_once(self.delayed_init, 1)
    
    def delayed_init(self, dt):
        self.ids.lb_title.text = APP_TITLE
        self.ids.lb_subtitle.text = APP_SUBTITLE        
        self.ids.img_pemkab.source = f'assets/images/{IMG_LOGO_PEMKAB}'
        self.ids.img_dishub.source = f'assets/images/{IMG_LOGO_DISHUB}'
        self.ids.lb_pemkab.text = LB_PEMKAB
        self.ids.lb_dishub.text = LB_DISHUB
        self.ids.lb_unit.text = LB_UNIT
        self.ids.lb_unit_address.text = LB_UNIT_ADDRESS
        
        Clock.schedule_interval(self.regular_update_display, 1)
        Clock.schedule_interval(self.regular_update_connection, UPDATE_CONNECTION_INTERVAL)

    def on_enter(self):
        self.exec_reload_database()
        self.exec_reload_table()

    def regular_update_display(self, dt):
        global flag_conn_stat
        global count_starting, count_get_data
        global dt_user, dt_no_antri, dt_no_pol, dt_no_uji, dt_nama, dt_jns_kend
        global dt_load_flag, db_load_left_value, db_load_right_value, db_load_total_value, db_load_flag, dt_id_user
        global dt_brake_flag, db_brake_left_value, db_brake_right_value, db_brake_total_value, db_brake_difference_value, db_brake_flag
        global dt_handbrake_flag, db_handbrake_left_value, db_handbrake_right_value, db_handbrake_total_value, db_handbrake_difference_value, db_handbrake_flag
        global dt_load_total_value, dt_brake_total_value, dt_brake_efficiency_value, dt_brake_difference_value, dt_handbrake_total_value, dt_handbrake_efficiency_value, dt_handbrake_difference_value
        global dt_test_number
        
        try:
            screen_home = self.screen_manager.get_screen('screen_home')
            screen_login = self.screen_manager.get_screen('screen_login')
            screen_menu = self.screen_manager.get_screen('screen_menu')
            screen_calibration = self.screen_manager.get_screen('screen_calibration')
            screen_add_data = self.screen_manager.get_screen('screen_add_data')
            screen_add_queue = self.screen_manager.get_screen('screen_add_queue')

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
            screen_calibration.ids.lb_time.text = str(time.strftime("%H:%M:%S", time.localtime()))
            screen_calibration.ids.lb_date.text = str(time.strftime("%d/%m/%Y", time.localtime()))
            screen_add_data.ids.lb_time.text = str(time.strftime("%H:%M:%S", time.localtime()))
            screen_add_data.ids.lb_date.text = str(time.strftime("%d/%m/%Y", time.localtime()))
            screen_add_queue.ids.lb_time.text = str(time.strftime("%H:%M:%S", time.localtime()))
            screen_add_queue.ids.lb_date.text = str(time.strftime("%d/%m/%Y", time.localtime()))

            screen_load_meter.ids.lb_time.text = str(time.strftime("%H:%M:%S", time.localtime()))
            screen_load_meter.ids.lb_date.text = str(time.strftime("%d/%m/%Y", time.localtime()))
            screen_brake_meter.ids.lb_time.text = str(time.strftime("%H:%M:%S", time.localtime()))
            screen_brake_meter.ids.lb_date.text = str(time.strftime("%d/%m/%Y", time.localtime()))
            screen_handbrake_meter.ids.lb_time.text = str(time.strftime("%H:%M:%S", time.localtime()))
            screen_handbrake_meter.ids.lb_date.text = str(time.strftime("%d/%m/%Y", time.localtime()))
            screen_resume.ids.lb_time.text = str(time.strftime("%H:%M:%S", time.localtime()))
            screen_resume.ids.lb_date.text = str(time.strftime("%d/%m/%Y", time.localtime()))

            self.ids.lb_dash_antri.text = str(dt_dash_antri)
            self.ids.lb_dash_belum_uji.text = str(dt_dash_belum_uji)
            self.ids.lb_dash_sudah_uji.text = str(dt_dash_sudah_uji)

            screen_load_meter.ids.lb_load_l_val.text = str(int(db_load_left_value[dt_test_number]))
            screen_load_meter.ids.lb_load_r_val.text = str(int(db_load_right_value[dt_test_number]))
            screen_load_meter.ids.lb_load_total_val.text = str(int(db_load_total_value[dt_test_number]))
            screen_brake_meter.ids.lb_brake_l_val.text = str(int(db_brake_left_value[dt_test_number]))
            screen_brake_meter.ids.lb_brake_r_val.text = str(int(db_brake_right_value[dt_test_number]))
            screen_brake_meter.ids.lb_brake_total_val.text = str(int(db_brake_total_value[dt_test_number]))
            screen_handbrake_meter.ids.lb_handbrake_l_val.text = str(int(db_handbrake_left_value[dt_test_number]))
            screen_handbrake_meter.ids.lb_handbrake_r_val.text = str(int(db_handbrake_right_value[dt_test_number]))
            screen_handbrake_meter.ids.lb_handbrake_total_val.text = str(int(db_handbrake_total_value[dt_test_number]))

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

            if(count_starting <= 0):
                screen_load_meter.ids.lb_test_subtitle.text = "HASIL PENGUKURAN"
                screen_load_meter.ids.lb_load_l_val.text = str(int(db_load_left_value[dt_test_number]))
                screen_load_meter.ids.lb_load_r_val.text = str(int(db_load_right_value[dt_test_number]))
                screen_load_meter.ids.lb_load_total_val.text = str(int(db_load_total_value[dt_test_number]))
                screen_brake_meter.ids.lb_test_subtitle.text = "HASIL PENGUKURAN"
                screen_brake_meter.ids.lb_brake_l_val.text = str(int(db_brake_left_value[dt_test_number]))
                screen_brake_meter.ids.lb_brake_r_val.text = str(int(db_brake_right_value[dt_test_number]))
                screen_brake_meter.ids.lb_brake_total_val.text = str(int(db_brake_total_value[dt_test_number]))
                screen_handbrake_meter.ids.lb_test_subtitle.text = "HASIL PENGUKURAN"
                screen_handbrake_meter.ids.lb_handbrake_l_val.text = str(int(db_handbrake_left_value[dt_test_number]))
                screen_handbrake_meter.ids.lb_handbrake_r_val.text = str(int(db_handbrake_right_value[dt_test_number]))
                screen_handbrake_meter.ids.lb_handbrake_total_val.text = str(int(db_handbrake_total_value[dt_test_number]))
                    
                if(db_load_total_value[dt_test_number] <= STANDARD_MAX_AXLE_LOAD):
                    screen_load_meter.ids.lb_info.text = f"Ambang Batas Beban yang diperbolehkan adalah {STANDARD_MAX_AXLE_LOAD} kg.\nBerat Roda Kendaraan Anda Dalam Range Ambang Batas"
                else:
                    screen_load_meter.ids.lb_info.text = f"Ambang Batas Beban yang diperbolehkan adalah {STANDARD_MAX_AXLE_LOAD} kg.\nBerat Roda Kendaraan Anda Diluar Ambang Batas"

                if(db_brake_total_value[dt_test_number] <= STANDARD_MAX_BRAKE):
                    screen_brake_meter.ids.lb_info.text = f"Ambang Batas Beban yang diperbolehkan adalah {STANDARD_MAX_AXLE_LOAD} kg.\nKekuatan Pengereman Kendaraan Anda Dalam Range Ambang Batas"
                else:
                    screen_brake_meter.ids.lb_info.text = f"Ambang Batas Beban yang diperbolehkan adalah {STANDARD_MAX_AXLE_LOAD} kg.\nKekuatan Pengereman Kendaraan Anda Diluar Ambang Batas"                

                if(db_handbrake_total_value[dt_test_number] <= STANDARD_MAX_HANDBRAKE):
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
                    screen_load_meter.ids.lb_test_result.text = f"S{dt_test_number + 1}\nTOTAL {int(db_load_total_value[dt_test_number])}"

                    screen_brake_meter.ids.lb_test_result.md_bg_color = colors['Green']['200']
                    screen_brake_meter.ids.lb_test_result.text_color = colors['Green']['700']
                    screen_brake_meter.ids.lb_test_result.text = f"S{dt_test_number + 1}\nTOTAL {int(db_brake_total_value[dt_test_number])}"

                    screen_handbrake_meter.ids.lb_test_result.md_bg_color = colors['Green']['200']
                    screen_handbrake_meter.ids.lb_test_result.text_color = colors['Green']['700']
                    screen_handbrake_meter.ids.lb_test_result.text = f"S{dt_test_number + 1}\nTOTAL {int(db_handbrake_total_value[dt_test_number])}"

            elif(count_get_data > 0):
                screen_load_meter.ids.lb_test_result.md_bg_color = "#EEEEEE"
                screen_load_meter.ids.lb_test_result.text = ""

                screen_brake_meter.ids.lb_test_result.md_bg_color = "#EEEEEE"
                screen_brake_meter.ids.lb_test_result.text = ""
                
                screen_handbrake_meter.ids.lb_test_result.md_bg_color = "#EEEEEE"
                screen_handbrake_meter.ids.lb_test_result.text = ""
            
            for i in range(12):
                if(dt_test_number == i):
                    screen_menu.ids[f'bt_S{i+1}'].md_bg_color = colors['Red']['A200']
                else:
                    screen_menu.ids[f'bt_S{i+1}'].md_bg_color = colors['Green']['200']

            if(not flag_conn_stat):
                self.ids.lb_comm.color = colors['Red']['A200']
                self.ids.lb_comm.text = 'PLC Tidak Terhubung'
                screen_home.ids.lb_comm.color = colors['Red']['A200']
                screen_home.ids.lb_comm.text = 'PLC Tidak Terhubung'
                screen_login.ids.lb_comm.color = colors['Red']['A200']
                screen_login.ids.lb_comm.text = 'PLC Tidak Terhubung'
                screen_menu.ids.lb_comm.color = colors['Red']['A200']
                screen_menu.ids.lb_comm.text = 'PLC Tidak Terhubung'
                screen_calibration.ids.lb_comm.color = colors['Red']['A200']
                screen_calibration.ids.lb_comm.text = 'PLC Tidak Terhubung'
                screen_add_data.ids.lb_comm.color = colors['Red']['A200']
                screen_add_data.ids.lb_comm.text = 'PLC Tidak Terhubung'
                screen_add_queue.ids.lb_comm.color = colors['Red']['A200']
                screen_add_queue.ids.lb_comm.text = 'PLC Tidak Terhubung'

                screen_load_meter.ids.lb_comm.color = colors['Red']['A200']
                screen_load_meter.ids.lb_comm.text = 'PLC Tidak Terhubung'
                screen_brake_meter.ids.lb_comm.color = colors['Red']['A200']
                screen_brake_meter.ids.lb_comm.text = 'PLC Tidak Terhubung'
                screen_handbrake_meter.ids.lb_comm.color = colors['Red']['A200']
                screen_handbrake_meter.ids.lb_comm.text = 'PLC Tidak Terhubung'
                screen_resume.ids.lb_comm.color = colors['Red']['A200']
                screen_resume.ids.lb_comm.text = 'PLC Tidak Terhubung'

            else:
                self.ids.lb_comm.color = colors['Blue']['200']
                self.ids.lb_comm.text = 'PLC Terhubung'
                screen_home.ids.lb_comm.color = colors['Blue']['200']
                screen_home.ids.lb_comm.text = 'PLC Terhubung'
                screen_login.ids.lb_comm.color = colors['Blue']['200']
                screen_login.ids.lb_comm.text = 'PLC Terhubung'
                screen_menu.ids.lb_comm.color = colors['Blue']['200']
                screen_menu.ids.lb_comm.text = 'PLC Terhubung'
                screen_calibration.ids.lb_comm.color = colors['Blue']['200']
                screen_calibration.ids.lb_comm.text = 'PLC Terhubung'
                screen_add_data.ids.lb_comm.color = colors['Blue']['200']
                screen_add_data.ids.lb_comm.text = 'PLC Terhubung'
                screen_add_queue.ids.lb_comm.color = colors['Blue']['200']
                screen_add_queue.ids.lb_comm.text = 'PLC Terhubung'

                screen_load_meter.ids.lb_comm.color = colors['Blue']['200']
                screen_load_meter.ids.lb_comm.text = 'PLC Terhubung'
                screen_brake_meter.ids.lb_comm.color = colors['Blue']['200']
                screen_brake_meter.ids.lb_comm.text = 'PLC Terhubung'
                screen_handbrake_meter.ids.lb_comm.color = colors['Blue']['200']
                screen_handbrake_meter.ids.lb_comm.text = 'PLC Terhubung'
                screen_resume.ids.lb_comm.color = colors['Blue']['200']
                screen_resume.ids.lb_comm.text = 'PLC Terhubung'

            if(self.screen_manager.current == 'screen_calibration'):
                MODBUS_CLIENT.connect()
                load_l_registers = MODBUS_CLIENT.read_holding_registers(REGISTER_DATA_LOAD_L, count=1, slave=1) #V1400
                load_r_registers = MODBUS_CLIENT.read_holding_registers(REGISTER_DATA_LOAD_R, count=1, slave=1) #V1410
                brake_l_registers = MODBUS_CLIENT.read_holding_registers(REGISTER_DATA_BRAKE_L, count=1, slave=1) #V1420
                brake_r_registers = MODBUS_CLIENT.read_holding_registers(REGISTER_DATA_BRAKE_R, count=1, slave=1) #V1430
                MODBUS_CLIENT.close()

                dt_load_l_val = int(self.unsigned_to_signed(load_l_registers.registers[0]))
                dt_load_r_val = int(self.unsigned_to_signed(load_r_registers.registers[0]))
                dt_brake_l_val = int(self.unsigned_to_signed(brake_l_registers.registers[0]))
                dt_brake_r_val = int(self.unsigned_to_signed(brake_r_registers.registers[0]))

                dt_load_l_val = dt_load_l_val if dt_load_l_val >= 0 and dt_load_l_val <= MAX_LOAD_DATA else 0
                dt_load_r_val = dt_load_r_val if dt_load_r_val >= 0 and dt_load_r_val <= MAX_LOAD_DATA else 0
                dt_brake_l_val = dt_brake_l_val if dt_brake_l_val >= 0 and dt_brake_l_val <= MAX_BRAKE_DATA else 0
                dt_brake_r_val = dt_brake_r_val if dt_brake_r_val >= 0 and dt_brake_r_val <= MAX_BRAKE_DATA else 0

                screen_calibration.ids.lb_load_l_val.text = str(dt_load_l_val)
                screen_calibration.ids.lb_load_r_val.text = str(dt_load_r_val)
                screen_calibration.ids.lb_brake_l_val.text = str(dt_brake_l_val)
                screen_calibration.ids.lb_brake_r_val.text = str(dt_brake_r_val)

            self.ids.bt_calibrate.disabled = False if dt_user != '' else True
            self.ids.bt_add_data.disabled = False if dt_user != '' else True
            self.ids.bt_add_queue.disabled = False if dt_user != '' else True
            self.ids.bt_logout.disabled = False if dt_user != '' else True

            self.ids.lb_operator.text = f'Login Sebagai: \n{dt_user}' if dt_user != '' else 'Silahkan Login'
            screen_home.ids.lb_operator.text = f'Login Sebagai: \n{dt_user}' if dt_user != '' else 'Silahkan Login'
            screen_login.ids.lb_operator.text = f'Login Sebagai: \n{dt_user}' if dt_user != '' else 'Silahkan Login'
            screen_menu.ids.lb_operator.text = f'Login Sebagai: \n{dt_user}' if dt_user != '' else 'Silahkan Login'
            screen_calibration.ids.lb_operator.text = f'Login Sebagai: \n{dt_user}' if dt_user != '' else 'Silahkan Login'
            screen_add_data.ids.lb_operator.text = f'Login Sebagai: \n{dt_user}' if dt_user != '' else 'Silahkan Login'
            screen_add_queue.ids.lb_operator.text = f'Login Sebagai: \n{dt_user}' if dt_user != '' else 'Silahkan Login'
            
            screen_load_meter.ids.lb_operator.text = f'Login Sebagai: \n{dt_user}' if dt_user != '' else 'Silahkan Login'
            screen_brake_meter.ids.lb_operator.text = f'Login Sebagai: \n{dt_user}' if dt_user != '' else 'Silahkan Login'
            screen_handbrake_meter.ids.lb_operator.text = f'Login Sebagai: \n{dt_user}' if dt_user != '' else 'Silahkan Login'
            screen_resume.ids.lb_operator.text = f'Login Sebagai: \n{dt_user}' if dt_user != '' else 'Silahkan Login'

            if dt_user != '':
                self.ids.img_user.source = f'https://{FTP_HOST}/sim_pkb/foto_user/{dt_foto_user}'
                screen_home.ids.img_user.source = f'https://{FTP_HOST}/sim_pkb/foto_user/{dt_foto_user}'
                screen_login.ids.img_user.source = f'https://{FTP_HOST}/sim_pkb/foto_user/{dt_foto_user}'
            else:
                self.ids.img_user.source = 'assets/images/icon-login.png'
                screen_home.ids.img_user.source = 'assets/images/icon-login.png'
                screen_login.ids.img_user.source = 'assets/images/icon-login.png'

        except Exception as e:
            toast_msg = f'Gagal Memperbaharui Tampilan'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")

    def regular_update_connection(self, dt):
        global flag_conn_stat

        try:
            MODBUS_CLIENT.connect()
            flag_conn_stat = MODBUS_CLIENT.connected
            MODBUS_CLIENT.close()
            
        except Exception as e:
            toast_msg = f'Gagal Memperbaharui Koneksi'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  
            flag_conn_stat = False

    def unsigned_to_signed(self, val):
        if val >= 32768:
            return val - 65536
        return val

    def regular_get_data(self, dt):
        global count_starting, count_get_data
        global flag_play, flag_conn_stat, flag_motor_brake
        global dt_load_flag, dt_brake_flag, dt_handbrake_flag
        global db_load_left_value, db_load_right_value, db_load_total_value, db_load_flag
        global db_brake_left_value, db_brake_right_value, db_brake_total_value, db_brake_difference_value, db_brake_flag
        global db_handbrake_left_value, db_handbrake_right_value, db_handbrake_total_value, db_handbrake_difference_value, db_handbrake_flag
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
                load_l_registers = MODBUS_CLIENT.read_holding_registers(REGISTER_DATA_LOAD_L, count=1, slave=1) #V1400
                load_r_registers = MODBUS_CLIENT.read_holding_registers(REGISTER_DATA_LOAD_R, count=1, slave=1) #V1410
                brake_l_registers = MODBUS_CLIENT.read_holding_registers(REGISTER_DATA_BRAKE_L, count=1, slave=1) #V1420
                brake_r_registers = MODBUS_CLIENT.read_holding_registers(REGISTER_DATA_BRAKE_R, count=1, slave=1) #V1430
                MODBUS_CLIENT.close()

            if self.screen_manager.current == 'screen_load_meter':
                db_load_left_value[dt_test_number] = int(self.unsigned_to_signed(load_l_registers.registers[0]))
                db_load_right_value[dt_test_number] = int(self.unsigned_to_signed(load_r_registers.registers[0]))

                db_load_left_value[dt_test_number] = db_load_left_value[dt_test_number] if db_load_left_value[dt_test_number] >= 0 and db_load_left_value[dt_test_number] <= MAX_LOAD_DATA else 0
                db_load_right_value[dt_test_number] = db_load_right_value[dt_test_number] if db_load_right_value[dt_test_number] >= 0 and db_load_right_value[dt_test_number] <= MAX_LOAD_DATA else 0

                db_load_total_value[dt_test_number] = int(db_load_left_value[dt_test_number] + db_load_right_value[dt_test_number])
                dt_load_total_value = int(np.sum(db_load_total_value))

                # Load test result status
                if(np.abs(int(np.sum(db_load_left_value)) - int(np.sum(db_load_right_value))) <= ((STANDARD_MAX_DIFFERENCE_AXLE_LOAD)/100) * int(dt_load_total_value)):
                    db_load_flag[dt_test_number] = 2
                    dt_load_flag = 2
                else:
                    db_load_flag[dt_test_number] = 1
                    dt_load_flag = 1

                Logger.info(f"{self.screen_manager.current}: DB Load Left = {db_load_left_value}, DB Load Right = {db_load_right_value}, DB Load Total = {db_load_total_value}")
                Logger.info(f"{self.screen_manager.current}: DB Load Left = {db_load_left_value[dt_test_number]}, DB Load Right = {db_load_right_value[dt_test_number]}, DB Load Total = {db_load_total_value[dt_test_number]}")
                Logger.info(f"{self.screen_manager.current}: DB Load Flag = {db_load_flag}")

            if self.screen_manager.current == 'screen_brake_meter':
                db_brake_left_value[dt_test_number] = int(self.unsigned_to_signed(brake_l_registers.registers[0]))
                db_brake_right_value[dt_test_number] = int(self.unsigned_to_signed(brake_r_registers.registers[0]))

                db_brake_left_value[dt_test_number] = db_brake_left_value[dt_test_number] if db_brake_left_value[dt_test_number] >= 0 and db_brake_left_value[dt_test_number] <= MAX_BRAKE_DATA else 0
                db_brake_right_value[dt_test_number] = db_brake_right_value[dt_test_number] if db_brake_right_value[dt_test_number] >= 0 and db_brake_right_value[dt_test_number] <= MAX_BRAKE_DATA else 0

                # Initialize total for brake test
                db_brake_total_value[dt_test_number] = int(db_brake_left_value[dt_test_number] + db_brake_right_value[dt_test_number])

                # Efficiency: (total brake / total load) * 100
                if dt_load_total_value > 0:
                    dt_brake_efficiency_value = np.round(
                        (db_brake_total_value[dt_test_number] / dt_load_total_value) * 100, 1
                    )
                else:
                    dt_brake_efficiency_value = 0  # or np.nan, or None
                    Logger.warning(f"{self.screen_manager.current}: dt_load_total_value is zero. Cannot calculate efficiency.")

                # Brake difference: |left - right| / load * 100
                if db_load_total_value[dt_test_number] > 0:
                    db_brake_difference_value[dt_test_number] = np.round(
                        (np.abs(db_brake_left_value[dt_test_number] - db_brake_right_value[dt_test_number]) / db_load_total_value[dt_test_number]) * 100, 1
                    )
                else:
                    db_brake_difference_value[dt_test_number] = 0
                    Logger.warning(f"{self.screen_manager.current}: db_load_total_value[{dt_test_number}] is zero. Cannot calculate brake difference.")

                # Aggregate brake totals
                dt_brake_total_value = int(np.sum(db_brake_total_value))

                # Overall efficiency
                if dt_load_total_value != 0:
                    dt_brake_efficiency_value = np.round((dt_brake_total_value / dt_load_total_value) * 100, 1)
                else:
                    dt_brake_efficiency_value = 0.0
                    Logger.warning(f"{self.screen_manager.current}: dt_load_total_value is zero. Cannot calculate total brake efficiency.")

                # Overall difference
                dt_brake_difference_value = int(np.sum(db_brake_difference_value))

                # Brake test result status
                if(db_brake_difference_value[dt_test_number] <= STANDARD_MAX_DIFFERENCE_BRAKE):
                    db_brake_flag[dt_test_number] = 2
                    dt_brake_flag = 2
                else:
                    db_brake_flag[dt_test_number] = 1
                    dt_brake_flag = 1

                # Logging
                Logger.info(f"{self.screen_manager.current}: DB Brake Left = {db_brake_left_value}, "
                            f"DB Brake Right = {db_brake_right_value}, "
                            f"DB Brake Total = {db_brake_total_value}, "
                            f"DB Brake Difference = {db_brake_difference_value}")

                Logger.info(f"{self.screen_manager.current}: For test {dt_test_number}: "
                            f"DB Brake Left = {db_brake_left_value[dt_test_number]}, "
                            f"DB Brake Right = {db_brake_right_value[dt_test_number]}, "
                            f"DB Brake Total = {db_brake_total_value[dt_test_number]}, "
                            f"DB Brake Difference = {db_brake_difference_value[dt_test_number]}")
                Logger.info(f"{self.screen_manager.current}: DB Brake Flag = {db_brake_flag}")

            if self.screen_manager.current == 'screen_handbrake_meter':
                db_handbrake_left_value[dt_test_number] = int(self.unsigned_to_signed(brake_l_registers.registers[0]))
                db_handbrake_right_value[dt_test_number] = int(self.unsigned_to_signed(brake_r_registers.registers[0]))

                db_handbrake_left_value[dt_test_number] = db_handbrake_left_value[dt_test_number] if db_handbrake_left_value[dt_test_number] >= 0 and db_handbrake_left_value[dt_test_number] <= MAX_BRAKE_DATA else 0
                db_handbrake_right_value[dt_test_number] = db_handbrake_right_value[dt_test_number] if db_handbrake_right_value[dt_test_number] >= 0 and db_handbrake_right_value[dt_test_number] <= MAX_BRAKE_DATA else 0

                # Initialize total for handbrake test
                db_handbrake_total_value[dt_test_number] = int(db_handbrake_left_value[dt_test_number] + db_handbrake_right_value[dt_test_number])

                # Handbrake efficiency: use handbrake total and dt_jbb (assuming jbb = axle load or test standard)
                if dt_jbb > 0:
                    dt_handbrake_efficiency_value = np.round(
                        (db_handbrake_total_value[dt_test_number] / float(dt_jbb)) * 100, 1
                    )
                else:
                    dt_handbrake_efficiency_value = 0
                    Logger.warning(f"{self.screen_manager.current}: dt_jbb is invalid ({dt_jbb}). Setting efficiency to 0.")

                # Handbrake difference: |left - right| / load * 100
                if db_load_total_value[dt_test_number] > 0:
                    db_handbrake_difference_value[dt_test_number] = np.round(
                        (np.abs(db_handbrake_left_value[dt_test_number] - db_handbrake_right_value[dt_test_number])
                        / db_load_total_value[dt_test_number]) * 100, 1
                    )
                else:
                    db_handbrake_difference_value[dt_test_number] = 0
                    Logger.warning(f"{self.screen_manager.current}: db_load_total_value[{dt_test_number}] is zero. Setting difference to 0.")

                # Aggregate handbrake totals
                dt_handbrake_total_value = int(np.sum(db_handbrake_total_value))

                # Overall handbrake efficiency
                if dt_load_total_value != 0:
                    dt_handbrake_efficiency_value = np.round(
                        (dt_handbrake_total_value / dt_load_total_value) * 100, 1
                    )
                else:
                    dt_handbrake_efficiency_value = 0
                    Logger.warning(f"{self.screen_manager.current}: dt_load_total_value is zero. Overall efficiency set to 0.")

                # Sum of percentage differences? Be careful — summing % can be misleading
                dt_handbrake_difference_value = int(np.sum(db_handbrake_difference_value))

                # HandBrake test result status
                if(dt_handbrake_efficiency_value >= STANDARD_MIN_EFFICIENCY_HANDBRAKE):
                    db_handbrake_flag[dt_test_number] = 2
                    dt_handbrake_flag = 2
                else:
                    db_handbrake_flag[dt_test_number] = 1
                    dt_handbrake_flag = 1

                # Logging
                Logger.info(f"{self.screen_manager.current}: DB Handbrake Left = {db_handbrake_left_value}, "
                            f"DB Handbrake Right = {db_handbrake_right_value}, "
                            f"DB Handbrake Total = {db_handbrake_total_value}, "
                            f"DB Handbrake Difference = {db_handbrake_difference_value}")

                Logger.info(f"{self.screen_manager.current}: Test {dt_test_number} - "
                            f"Handbrake Left = {db_handbrake_left_value[dt_test_number]}, "
                            f"Right = {db_handbrake_right_value[dt_test_number]}, "
                            f"Total = {db_handbrake_total_value[dt_test_number]}, "
                            f"Difference = {db_handbrake_difference_value[dt_test_number]}%")
                Logger.info(f"{self.screen_manager.current}: DB Handbrake Flag = {db_handbrake_flag}")

        except Exception as e:
            toast_msg = f'Gagal Mengambil Data dari PLC'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")

    def exec_reload_database(self):
        global mydb
        try:
            mydb = mysql.connector.connect(host = DB_HOST,user = DB_USER,password = DB_PASSWORD,database = DB_NAME)
        except Exception as e:
            toast_msg = f'Gagal Menginisiasi Database'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_reload_table(self):
        global mydb, db_antrian
        global db_merk, db_bahan_bakar, db_warna
        global dt_dash_antri, dt_dash_belum_uji, dt_dash_sudah_uji
        global window_size_x, window_size_y

        try:
            tb_antrian = mydb.cursor()
            today = str(time.strftime("%Y-%m-%d", time.localtime()))
            delete_query = f"DELETE FROM {TB_DATA} WHERE DATE(tgl_daftar) != %s"
            tb_antrian.execute(delete_query, (today,))
            mydb.commit()
            toast_msg = f'Berhasil menghapus data kemarin'
        except Exception as e:
            toast_msg = f'Gagal menghapus data kemarin'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

        try:
            tb_merk = mydb.cursor()
            tb_merk.execute(f"SELECT ID, DESCRIPTION FROM {TB_MERK}")
            result_tb_merk = tb_merk.fetchall()
            mydb.commit()
            db_merk = np.array(result_tb_merk)

            tb_bahan_bakar = mydb.cursor()
            tb_bahan_bakar.execute(f"SELECT ID, DESCRIPTION FROM {TB_BAHAN_BAKAR}")
            result_tb_bahan_bakar = tb_bahan_bakar.fetchall()
            mydb.commit()
            db_bahan_bakar = np.array(result_tb_bahan_bakar)

            tb_warna = mydb.cursor()
            tb_warna.execute(f"SELECT id_warna, nama FROM {TB_WARNA}")
            result_tb_warna = tb_warna.fetchall()
            mydb.commit()
            db_warna = np.array(result_tb_warna)

            tb_antrian = mydb.cursor()
            tb_antrian.execute(f"SELECT noantrian, nopol, nouji, statusuji, merk, type, idjeniskendaraan, jbb, berat_kosong, bahan_bakar, warna, load_flag, brake_flag, handbrake_flag FROM {TB_DATA}")
            result_tb_antrian = tb_antrian.fetchall()
            mydb.commit()
            if result_tb_antrian is None:
                toast('Data Tabel cekident kosong')
                dt_dash_antri = dt_dash_belum_uji = dt_dash_sudah_uji = 0
            else:
                db_antrian = np.array(result_tb_antrian).T
                db_pendaftaran = np.array(result_tb_antrian)
                dt_dash_antri = db_pendaftaran[:,11].size
                dt_dash_belum_uji = np.where(db_pendaftaran[:,11] == 0)[0].size
                dt_dash_sudah_uji = np.where(db_pendaftaran[:,11] == 1)[0].size + np.where(db_pendaftaran[:,11] == 2)[0].size
        except Exception as e:
            toast_msg = f'Gagal mengambil data antrian harian'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

        try:            
            layout_list = self.ids.layout_list
            layout_list.clear_widgets(children=None)
        except Exception as e:
            toast_msg = f'Gagal menghapus widget tabel'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")   
        
        try:           
            layout_list = self.ids.layout_list
            for i in range(db_antrian[0,:].size):
                layout_list.add_widget(
                    MDCard(
                        MDLabel(text=f"{db_antrian[0, i]}", size_hint_x= 0.05),
                        MDLabel(text=f"{db_antrian[1, i]}", size_hint_x= 0.07),
                        MDLabel(text=f"{db_antrian[2, i]}", size_hint_x= 0.08),
                        MDLabel(text='Berkala' if db_antrian[3, i] == 'B' else 'Uji Ulang' if (db_antrian[3, i]) == 'U' else 'Baru' if (db_antrian[3, i]) == 'BR' else 'Numpang Uji' if (db_antrian[3, i]) == 'NB' else 'Mutasi', size_hint_x= 0.07),
                        MDLabel(text='-' if db_antrian[4, i] == None else f"{db_merk[np.where(db_merk == db_antrian[4, i])[0][0],1]}" , size_hint_x= 0.08),
                        MDLabel(text=f"{db_antrian[5, i]}", size_hint_x= 0.07),
                        MDLabel(text=f"{db_antrian[6, i]}", size_hint_x= 0.15),
                        MDLabel(text=f"{db_antrian[7, i]}", size_hint_x= 0.05),
                        MDLabel(text=f"{db_antrian[8, i]}", size_hint_x= 0.05),
                        MDLabel(text='-' if db_antrian[9, i] == None else f"{db_bahan_bakar[np.where(db_bahan_bakar == db_antrian[9, i])[0][0],1]}" , size_hint_x= 0.08),
                        MDLabel(text='-' if db_antrian[10, i] == None else f"{db_warna[np.where(db_warna == db_antrian[10, i])[0][0],1]}" , size_hint_x= 0.11),
                        MDLabel(text='Lulus' if (int(db_antrian[11, i]) == 2) else 'Tidak Lulus' if (int(db_antrian[11, i]) == 1) else 'Belum Diuji', size_hint_x= 0.08),
                        MDLabel(text='Lulus' if (int(db_antrian[12, i]) == 2) else 'Tidak Lulus' if (int(db_antrian[12, i]) == 1) else 'Belum Diuji', size_hint_x= 0.07),
                        MDLabel(text='Lulus' if (int(db_antrian[13, i]) == 2) else 'Tidak Lulus' if (int(db_antrian[13, i]) == 1) else 'Belum Diuji', size_hint_x= 0.07),

                        ripple_behavior = True,
                        on_press = self.on_antrian_row_press,
                        padding = 20,
                        id=f"card_antrian{i}",
                        size_hint_y=None,
                        height=dp(int(60 * 800 / window_size_y)),
                        )
                    )
        except Exception as e:
            toast_msg = f'Gagal reload tabel'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")   

    def on_antrian_row_press(self, instance):
        global mydb, db_antrian, db_merk, db_bahan_bakar, db_warna
        global dt_no_antri, dt_no_pol, dt_no_uji, dt_sts_uji
        global dt_merk, dt_type, dt_jns_kend, dt_jbb, dt_brt_ksg, dt_bhn_bkr, dt_warna, dt_load_flag, dt_brake_flag, dt_handbrake_flag
        global dt_id_user, dt_foto_user

        try:
            row = int(str(instance.id).replace("card_antrian",""))
            dt_no_antri             = db_antrian[0, row]
            dt_no_pol               = db_antrian[1, row]
            dt_no_uji               = db_antrian[2, row]
            dt_sts_uji              = db_antrian[3, row]
            dt_merk                 = db_antrian[4, row]
            dt_type                 = db_antrian[5, row]
            dt_jns_kend             = db_antrian[6, row]
            dt_jbb                  = db_antrian[7, row]
            dt_brt_ksg              = db_antrian[8, row]
            dt_bhn_bkr              = db_antrian[9, row]
            dt_warna                = db_antrian[10, row]
            dt_load_flag            = db_antrian[11, row]
            dt_brake_flag           = db_antrian[12, row]
            dt_handbrake_flag       = db_antrian[13, row]

            self.exec_navigate_menu()

        except Exception as e:
            toast_msg = f'Gagal mengeksekusi perintah dari baris tabel'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_logout(self):
        global dt_user

        dt_user = ""
        self.screen_manager.current = 'screen_login'

    def exec_navigate_home(self):
        try:
            self.screen_manager.current = 'screen_home'

        except Exception as e:
            toast_msg = f'Terjadi kesalahan saat berpindah ke halaman Beranda'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_navigate_login(self):
        global dt_user
        try:
            if (dt_user == ""):
                self.screen_manager.current = 'screen_login'
            else:
                toast_msg = f"Anda sudah login sebagai {dt_user}"
                toast(toast_msg)
                Logger.info(f"{self.name}: {toast_msg}")

        except Exception as e:
            toast_msg = f'Terjadi kesalahan saat berpindah ke halaman Login'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_navigate_menu(self):
        global dt_load_flag, dt_brake_flag, dt_handbrake_flag, dt_no_antri, dt_user

        if (dt_user != ''):
            if (int(dt_load_flag) == 0 or int(dt_brake_flag) == 0 or int(dt_handbrake_flag) == 0):
                self.screen_manager.current = 'screen_menu'
            else:
                toast_msg = f'No. Antrian {dt_no_antri} Sudah Tes'
                toast(toast_msg)
                Logger.info(f"{self.name}: {toast_msg}")
        else:
            toast_msg = f'Silahkan Login Untuk Melakukan Pengujian'
            toast(toast_msg)
            Logger.info(f"{self.name}: {toast_msg}")      

    def exec_navigate_calibration(self):
        global dt_user
        try:
            self.screen_manager.current = 'screen_calibration'

        except Exception as e:
            toast_msg = f'Error Navigate to Calibration Screen: {e}'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_navigate_add_data(self):
        global dt_user
        try:
            self.screen_manager.current = 'screen_add_data'

        except Exception as e:
            toast_msg = f'Error Navigate to Add Data Screen: {e}'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_navigate_add_queue(self):
        global dt_user
        try:
            self.screen_manager.current = 'screen_add_queue'

        except Exception as e:
            toast_msg = f'Error Navigate to Add Queue Screen: {e}'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_navigate_main(self):
        try:
            self.screen_manager.current = 'screen_main'

        except Exception as e:
            toast_msg = f'Terjadi kesalahan saat berpindah ke halaman Utama'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

class ScreenCalibration(MDScreen):
    def __init__(self, **kwargs):
        super(ScreenCalibration, self).__init__(**kwargs)
        Clock.schedule_once(self.delayed_init, 1)
    
    def delayed_init(self, dt):
        self.ids.lb_title.text = APP_TITLE
        self.ids.lb_subtitle.text = APP_SUBTITLE
        self.ids.img_pemkab.source = f'assets/images/{IMG_LOGO_PEMKAB}'
        self.ids.img_dishub.source = f'assets/images/{IMG_LOGO_DISHUB}'
        self.ids.lb_pemkab.text = LB_PEMKAB
        self.ids.lb_dishub.text = LB_DISHUB
        self.ids.lb_unit.text = LB_UNIT
        self.ids.lb_unit_address.text = LB_UNIT_ADDRESS

    def on_enter(self):
        pass

    def on_leave(self):
        pass

    def exec_calibrate_load_l_start(self):
        global flag_conn_stat
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_register(1722, 1, slave=1) #V1210
                MODBUS_CLIENT.write_coil(3093, True, slave=1) #M21
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send exec_calibrate_load_l_start data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def rel_calibrate_load_l_start(self):
        global flag_conn_stat
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_coil(3093, False, slave=1) #M21
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send rel_calibrate_load_l_start data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}") 

    def exec_calibrate_load_l_zero(self):
        global flag_conn_stat
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_register(1724, 0, slave=1) #V1212
                MODBUS_CLIENT.write_coil(3094, True, slave=1) #M22
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send exec_calibrate_load_l_zero data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def rel_calibrate_load_l_zero(self):
        global flag_conn_stat
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_coil(3094, False, slave=1) # M22
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send rel_calibrate_load_l_zero data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")

    def exec_calibrate_load_l_value1(self):
        global flag_conn_stat
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_register(1726, int(self.ids.tx_calibrate_load_l_value1.text), slave=1) #V1214
                MODBUS_CLIENT.write_coil(3095, True, slave=1) #M23
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send exec_calibrate_load_l_value1 data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def rel_calibrate_load_l_value1(self):
        global flag_conn_stat
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_coil(3095, False, slave=1) # M23
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send rel_calibrate_load_l_value1 data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")

    def exec_calibrate_load_l_value2(self):
        global flag_conn_stat
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_register(1728, int(self.ids.tx_calibrate_load_l_value2.text), slave=1) #V1216
                MODBUS_CLIENT.write_coil(3096, True, slave=1) #M24
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send exec_calibrate_load_l_value2 data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def rel_calibrate_load_l_value2(self):
        global flag_conn_stat
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_coil(3096, False, slave=1) # M24
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send rel_calibrate_load_l_value2 data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")

    def exec_calibrate_load_l_stop(self):
        global flag_conn_stat
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_register(1730, 2, slave=1) #V1218
                MODBUS_CLIENT.write_coil(3097, True, slave=1) #M25
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send exec_calibrate_load_l_stop data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}") 

    def rel_calibrate_load_l_stop(self):
        global flag_conn_stat
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_coil(3097, False, slave=1) # M25
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send rel_calibrate_load_l_stop data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")

    def exec_calibrate_load_r_start(self):
        global flag_conn_stat
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_register(1752, 1, slave=1) #V1240
                MODBUS_CLIENT.write_coil(3193, True, slave=1) #M121
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send exec_calibrate_load_r_start data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def rel_calibrate_load_r_start(self):
        global flag_conn_stat
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_coil(3193, False, slave=1) # M121
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send rel_calibrate_load_r_start data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")

    def exec_calibrate_load_r_zero(self):
        global flag_conn_stat
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_register(1754, 0, slave=1) #V1242
                MODBUS_CLIENT.write_coil(3194, True, slave=1) #M122
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send exec_calibrate_load_r_zero data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def rel_calibrate_load_r_zero(self):
        global flag_conn_stat
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_coil(3194, False, slave=1) # M122
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send rel_calibrate_load_r_zero data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")
            
    def exec_calibrate_load_r_value1(self):
        global flag_conn_stat
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_register(1756, int(self.ids.tx_calibrate_load_r_value1.text), slave=1) #V1244
                MODBUS_CLIENT.write_coil(3195, True, slave=1) #M123
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send exec_calibrate_load_r_value1 data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def rel_calibrate_load_r_value1(self):
        global flag_conn_stat
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_coil(3195, False, slave=1) # M123
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send rel_calibrate_load_r_value1 data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")

    def exec_calibrate_load_r_value2(self):
        global flag_conn_stat
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_register(1758, int(self.ids.tx_calibrate_load_r_value2.text), slave=1) #V1246
                MODBUS_CLIENT.write_coil(3196, True, slave=1) #M124
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send exec_calibrate_load_r_value2 data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def rel_calibrate_load_r_value2(self):
        global flag_conn_stat
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_coil(3196, False, slave=1) # M124
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send rel_calibrate_load_r_value2 data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")

    def exec_calibrate_load_r_stop(self):
        global flag_conn_stat
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_register(1760, 2, slave=1) #V1248
                MODBUS_CLIENT.write_coil(3197, True, slave=1) #M125
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send exec_calibrate_load_r_stop data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}") 

    def rel_calibrate_load_r_stop(self):
        global flag_conn_stat
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_coil(3197, False, slave=1) # M125
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send rel_calibrate_load_r_stop data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")

    def exec_calibrate_brake_l_start(self):
        global flag_conn_stat
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_register(1782, 1, slave=1) #V1270
                MODBUS_CLIENT.write_coil(3293, True, slave=1) #M221
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send exec_calibrate_brake_l_start data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def rel_calibrate_brake_l_start(self):
        global flag_conn_stat
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_coil(3293, False, slave=1) # M221
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send rel_calibrate_brake_l_start data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")

    def exec_calibrate_brake_l_zero(self):
        global flag_conn_stat
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_register(1784, 0, slave=1) #V1272
                MODBUS_CLIENT.write_coil(3294, True, slave=1) #M222
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send exec_calibrate_brake_l_zero data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def rel_calibrate_brake_l_zero(self):
        global flag_conn_stat
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_coil(3294, False, slave=1) # M222
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send rel_calibrate_brake_l_zero data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")

    def exec_calibrate_brake_l_value1(self):
        global flag_conn_stat
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_register(1786, int(self.ids.tx_calibrate_brake_l_value1.text), slave=1) #V1274
                MODBUS_CLIENT.write_coil(3295, True, slave=1) #M223
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send exec_calibrate_brake_l_value1 data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def rel_calibrate_brake_l_value1(self):
        global flag_conn_stat
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_coil(3295, False, slave=1) # M223
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send rel_calibrate_brake_l_value1 data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")

    def exec_calibrate_brake_l_value2(self):
        global flag_conn_stat
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_register(1788, int(self.ids.tx_calibrate_brake_l_value2.text), slave=1) #V1276
                MODBUS_CLIENT.write_coil(3296, True, slave=1) #M224
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send exec_calibrate_brake_l_value2 data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def rel_calibrate_brake_l_value2(self):
        global flag_conn_stat
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_coil(3296, False, slave=1) # M224
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send rel_calibrate_brake_l_value2 data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")

    def exec_calibrate_brake_l_stop(self):
        global flag_conn_stat
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_register(1790, 2, slave=1) #V1278
                MODBUS_CLIENT.write_coil(3297, True, slave=1) #2M25
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send exec_calibrate_brake_l_stop data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}") 

    def rel_calibrate_brake_l_stop(self):
        global flag_conn_stat
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_coil(3297, False, slave=1) # M225
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send rel_calibrate_brake_l_stop data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")

    def exec_calibrate_brake_r_start(self):
        global flag_conn_stat
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_register(1812, 1, slave=1) #V1300
                MODBUS_CLIENT.write_coil(3393, True, slave=1) #M321
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send exec_calibrate_brake_r_start data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def rel_calibrate_brake_r_start(self):
        global flag_conn_stat
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_coil(3393, False, slave=1) # M321
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send rel_calibrate_brake_r_start data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")

    def exec_calibrate_brake_r_zero(self):
        global flag_conn_stat
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_register(1814, 0, slave=1) #V1302
                MODBUS_CLIENT.write_coil(3394, True, slave=1) #M322
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send exec_calibrate_brake_r_zero data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def rel_calibrate_brake_r_zero(self):
        global flag_conn_stat
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_coil(3394, False, slave=1) # M322
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send rel_calibrate_brake_r_zero data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")
            
    def exec_calibrate_brake_r_value1(self):
        global flag_conn_stat
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_register(1816, int(self.ids.tx_calibrate_brake_r_value1.text), slave=1) #V1304
                MODBUS_CLIENT.write_coil(3395, True, slave=1) #M123
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send exec_calibrate_brake_r_value1 data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def rel_calibrate_brake_r_value1(self):
        global flag_conn_stat
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_coil(3395, False, slave=1) # M323
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send rel_calibrate_brake_r_value1 data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")

    def exec_calibrate_brake_r_value2(self):
        global flag_conn_stat
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_register(1818, int(int(self.ids.tx_calibrate_brake_r_value2.text)), slave=1) #V1306
                MODBUS_CLIENT.write_coil(3396, True, slave=1) #M324
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send exec_calibrate_brake_r_value2 data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def rel_calibrate_brake_r_value2(self):
        global flag_conn_stat
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_coil(3396, False, slave=1) # M324
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send rel_calibrate_brake_r_value2 data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")

    def exec_calibrate_brake_r_stop(self):
        global flag_conn_stat
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_register(1820, 2, slave=1) #V1308
                MODBUS_CLIENT.write_coil(3397, True, slave=1) #M325
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send exec_calibrate_brake_r_stop data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}") 

    def rel_calibrate_brake_r_stop(self):
        global flag_conn_stat
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_coil(3397, False, slave=1) # M325
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send rel_calibrate_brake_r_stop data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")

    def exec_motor_brake_on(self):
        global flag_conn_stat
        global flag_motor_brake
        
        flag_motor_brake = True
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_coil(3075, True, slave=1) #M3
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send exec_motor_brake_on data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def rel_motor_brake_on(self):
        global flag_conn_stat
        global flag_motor_brake

        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_coil(3075, False, slave=1) #M3
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send rel_motor_brake_on data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_motor_brake_off(self):
        global flag_conn_stat
        global flag_motor_brake

        flag_motor_brake = False
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_coil(3076, True, slave=1) #M4
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send exec_motor_brake_off data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def rel_motor_brake_off(self):
        global flag_conn_stat
        global flag_motor_brake

        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_coil(3076, False, slave=1) #M4
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send rel_motor_brake_on data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_navigate_main(self):
        try:
            self.screen_manager.current = 'screen_main'

        except Exception as e:
            toast_msg = f'Terjadi kesalahan saat berpindah ke halaman Utama'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

class ScreenAddData(MDScreen):
    def __init__(self, **kwargs):
        super(ScreenAddData, self).__init__(**kwargs)
        Clock.schedule_once(self.delayed_init, 1)
    
    def delayed_init(self, dt):
        self.ids.lb_title.text = APP_TITLE
        self.ids.lb_subtitle.text = APP_SUBTITLE
        self.ids.img_pemkab.source = f'assets/images/{IMG_LOGO_PEMKAB}'
        self.ids.img_dishub.source = f'assets/images/{IMG_LOGO_DISHUB}'
        self.ids.lb_pemkab.text = LB_PEMKAB
        self.ids.lb_dishub.text = LB_DISHUB
        self.ids.lb_unit.text = LB_UNIT
        self.ids.lb_unit_address.text = LB_UNIT_ADDRESS

    def exec_cancel(self):
        try:
            self.screen_manager.current = 'screen_main'

        except Exception as e:
            toast_msg = f'Terjadi kesalahan saat berpindah ke halaman Utama'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def on_enter(self):
        """Called when screen is entered — safe to initialize dropdowns here."""
        Clock.schedule_once(self.load_dropdowns, 0.1)  # Small delay to ensure UI is loaded

    def on_leave(self):
        """Clean up menus to avoid memory leaks or errors."""
        if hasattr(self, 'menu_merk') and self.menu_merk:
            self.menu_merk.dismiss()
            self.menu_merk = None
        if hasattr(self, 'menu_bahan_bakar') and self.menu_bahan_bakar:
            self.menu_bahan_bakar.dismiss()
            self.menu_bahan_bakar = None
        if hasattr(self, 'menu_warna') and self.menu_warna:
            self.menu_warna.dismiss()
            self.menu_warna = None

    def load_dropdowns(self, dt=None):
        """Initialize dropdown menus for Merk, Bahan Bakar, Warna."""
        try:
            # --- Merk Dropdown ---
            tb_merk = mydb.cursor()
            tb_merk.execute(f"SELECT ID, DESCRIPTION FROM {TB_MERK}")
            result_tb_merk = tb_merk.fetchall()
            if result_tb_merk:
                self.merk_items = [
                    {
                        "viewclass": "OneLineListItem",
                        "text": row[1],
                        "on_release": lambda x=row[1], id=row[0]: self.set_merk(x, id),
                    } for row in result_tb_merk
                ]
                self.menu_merk = MDDropdownMenu(
                    caller=self.ids.drop_merk,
                    items=self.merk_items,
                    width_mult=4,  # You can adjust this
                )
            else:
                self.menu_merk = None

            # --- Bahan Bakar Dropdown ---
            tb_bahan_bakar = mydb.cursor()
            tb_bahan_bakar.execute(f"SELECT ID, DESCRIPTION FROM {TB_BAHAN_BAKAR}")
            result_tb_bahan_bakar = tb_bahan_bakar.fetchall()
            if result_tb_bahan_bakar:
                self.bahan_bakar_items = [
                    {
                        "viewclass": "OneLineListItem",
                        "text": row[1],
                        "on_release": lambda x=row[1], id=row[0]: self.set_bahan_bakar(x, id),
                    } for row in result_tb_bahan_bakar
                ]
                self.menu_bahan_bakar = MDDropdownMenu(
                    caller=self.ids.drop_bahan_bakar,
                    items=self.bahan_bakar_items,
                    width_mult=4,
                )
            else:
                self.menu_bahan_bakar = None

            # --- Warna Dropdown ---
            tb_warna = mydb.cursor()
            tb_warna.execute(f"SELECT id_warna, nama FROM {TB_WARNA}")
            result_tb_warna = tb_warna.fetchall()
            if result_tb_warna:
                self.warna_items = [
                    {
                        "viewclass": "OneLineListItem",
                        "text": row[1],
                        "on_release": lambda x=row[1], id=row[0]: self.set_warna(x, id),
                    } for row in result_tb_warna
                ]
                self.menu_warna = MDDropdownMenu(
                    caller=self.ids.drop_warna,
                    items=self.warna_items,
                    width_mult=4,
                )
            else:
                self.menu_warna = None

        except Exception as e:
            toast(f"Error loading dropdowns: {str(e)}")
            Logger.error(f"ScreenAddData: Failed to load dropdowns - {e}")

    # Set functions for dropdown selection
    def set_merk(self, text_item, id_item):
        self.ids.drop_merk.text = text_item
        self.ids.drop_merk.merk_id = id_item
        if self.menu_merk:
            self.menu_merk.dismiss()

    def set_bahan_bakar(self, text_item, id_item):
        self.ids.drop_bahan_bakar.text = text_item
        self.ids.drop_bahan_bakar.bahan_bakar_id = id_item
        if self.menu_bahan_bakar:
            self.menu_bahan_bakar.dismiss()

    def set_warna(self, text_item, id_item):
        self.ids.drop_warna.text = text_item
        self.ids.drop_warna.warna_id = id_item
        if self.menu_warna:
            self.menu_warna.dismiss()
        
    def exec_register(self):
        try:
            dt_temp_no_uji = self.ids.tx_nouji.text.strip()
            dt_temp_no_pol = self.ids.tx_nopol.text.strip()

            if not dt_temp_no_uji or not dt_temp_no_pol:
                toast("Nomor Uji dan Nomor Regristasi tidak boleh kosong!")
                return

            mycursor = mydb.cursor()

            check_nouji_sql = f"SELECT COUNT(*) FROM {TB_DATA_MASTER} WHERE NOUJI = %s"
            mycursor.execute(check_nouji_sql, (dt_temp_no_uji,))
            result_nouji = mycursor.fetchone()
            
            if result_nouji and result_nouji[0] > 0:
                toast("Nomor Uji ini sudah terdaftar!")
                Logger.warning(f"{self.name}: Upaya menambahkan duplikat NOUJI: {dt_temp_no_uji}")
                return 

            check_nopol_sql = f"SELECT COUNT(*) FROM {TB_DATA_MASTER} WHERE NOPOL = %s"
            mycursor.execute(check_nopol_sql, (dt_temp_no_pol,))
            result_nopol = mycursor.fetchone()

            if result_nopol and result_nopol[0] > 0:
                toast("Nomor Polisi ini sudah terdaftar!")
                Logger.warning(f"{self.name}: Upaya menambahkan duplikat NOPOL: {dt_temp_no_pol}")
                return 

            dt_temp_no_uji_new = self.ids.tx_nouji.text.strip()
            dt_temp_nama = self.ids.tx_nama.text.strip()
            dt_temp_alamat = self.ids.tx_alamat.text.strip()
            dt_temp_type = self.ids.tx_type.text.strip()
            dt_temp_jenis_kendaraan = self.ids.tx_jeniskendaraan.text.strip()
            dt_temp_jbb = self.ids.tx_jbb.text.strip()
            dt_temp_brt_ksg = self.ids.tx_beratkosong.text.strip()
            dt_temp_tgl_uji_terakhir = str(time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()))

            # self.ids.lb_temp_nama.text = f'{dt_temp_nama}'
            # self.ids.lb_temp_alamat.text = f'{dt_temp_alamat}'
            # self.ids.lb_temp_no_uji.text = f'{dt_temp_no_uji}'
            # self.ids.lb_temp_no_pol.text = f'{dt_temp_no_pol}'
            # self.ids.lb_temp_status_uji.text = 'Berkala' if dt_temp_status_uji == 'B' else 'Uji Ulang' if dt_temp_status_uji == 'U' else 'Baru' if dt_temp_status_uji == 'BR' else 'Numpang Uji' if dt_temp_status_uji == 'NB' else 'Mutasi'
            # self.ids.lb_temp_tgl_uji_terakhir.text = f'{dt_temp_tgl_uji_terakhir}'
            # self.ids.lb_temp_tgl_uji_habis.text = f'{dt_temp_tgl_uji_habis}'
            # self.ids.lb_temp_merk.text = '-' if dt_temp_id_merk == None else f"{db_merk[np.where(db_merk == dt_temp_id_merk)[0][0],1]}"
            # self.ids.lb_temp_type.text = f'{dt_temp_type}'
            # self.ids.lb_temp_jenis_kendaraan.text = f'{dt_temp_jenis_kendaraan}'
            # self.ids.lb_temp_warna.text = '-' if dt_temp_warna == None else f"{db_warna[np.where(db_warna == dt_temp_warna)[0][0],1]}"
            # self.ids.lb_temp_chasis.text = f'{dt_temp_chasis}'
            # self.ids.lb_temp_mesin.text = f'{dt_temp_mesin}'
            # self.ids.lb_temp_bahan_bakar.text = '-' if dt_temp_bhn_bkr == None else f"{db_bahan_bakar[np.where(db_bahan_bakar == dt_temp_bhn_bkr)[0][0],1]}"
            # self.ids.lb_temp_jbb.text = f'{dt_temp_jbb}'
            # self.ids.lb_temp_berat_kosong.text = f'{dt_temp_brt_ksg}'

            # Validate dropdowns have values selected
            if not hasattr(self.ids.drop_merk, 'merk_id'):
                toast("Pilih Merk!")
                return
            if not hasattr(self.ids.drop_bahan_bakar, 'bahan_bakar_id'):
                toast("Pilih Bahan Bakar!")
                return
            if not hasattr(self.ids.drop_warna, 'warna_id'):
                toast("Pilih Warna!")
                return

            dt_temp_id_merk = self.ids.drop_merk.merk_id
            dt_temp_bhn_bkr = self.ids.drop_bahan_bakar.bahan_bakar_id
            dt_temp_warna = self.ids.drop_warna.warna_id

            # Insert into database
            mycursor = mydb.cursor()
            sql = f"""
                INSERT INTO {TB_DATA_MASTER} 
                (NOUJI, NEW_NOUJI, NOPOL, NAMA, ALAMAT, MERK_ID, TYPE, idjeniskendaraan, BHN_BAKAR, JBB, BERATKOSONG, WARNA_KEND, TGL_UJI_PERDANA, TGL_UJI_TERAKHIR) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                dt_temp_no_uji,
                dt_temp_no_uji_new,
                dt_temp_no_pol,
                dt_temp_nama,
                dt_temp_alamat,
                dt_temp_id_merk,
                dt_temp_type,
                dt_temp_jenis_kendaraan,
                dt_temp_bhn_bkr,
                dt_temp_jbb,
                dt_temp_brt_ksg,
                dt_temp_warna,
                dt_temp_tgl_uji_terakhir,
                dt_temp_tgl_uji_terakhir
            )
            mycursor.execute(sql, values)
            mydb.commit()

            toast("Data berhasil didaftarkan")
            self.screen_manager.current = 'screen_main'

        except Exception as e:
            toast_msg = f'Terjadi kesalahan saat mendaftarkan data'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}") 

class ScreenAddQueue(MDScreen):
    def __init__(self, **kwargs):
        super(ScreenAddQueue, self).__init__(**kwargs)
        Clock.schedule_once(self.delayed_init, 1)
    
    def delayed_init(self, dt):
        self.ids.lb_title.text = APP_TITLE
        self.ids.lb_subtitle.text = APP_SUBTITLE
        self.ids.img_pemkab.source = f'assets/images/{IMG_LOGO_PEMKAB}'
        self.ids.img_dishub.source = f'assets/images/{IMG_LOGO_DISHUB}'
        self.ids.lb_pemkab.text = LB_PEMKAB
        self.ids.lb_dishub.text = LB_DISHUB
        self.ids.lb_unit.text = LB_UNIT
        self.ids.lb_unit_address.text = LB_UNIT_ADDRESS

    def on_enter(self):
        pass

    def on_leave(self):
        pass

    def exec_cancel(self):
        global dt_temp_no_uji, dt_temp_no_uji_new, dt_temp_no_wilayah, dt_temp_no_kendaraan, dt_temp_no_plat, dt_temp_no_pol
        global dt_temp_nama, dt_temp_no_hp, dt_temp_alamat, dt_temp_id_izin, dt_temp_wilayah, dt_temp_provinsi, dt_temp_kabupaten_kota, dt_temp_kecamatan
        global dt_temp_id_merk, dt_temp_id_subjenis, dt_temp_type, dt_temp_tahun_buat, dt_temp_silinder, dt_temp_warna, dt_temp_chasis, dt_temp_mesin, dt_temp_warna_plat
        global dt_temp_bhn_bkr, dt_temp_jbb, dt_temp_daya_motor, dt_temp_tgl_uji_terakhir, dt_temp_tgl_uji_habis, dt_temp_status_uji, dt_temp_status_penerbitan, dt_temp_jenis_kendaraan, dt_temp_kode_jenis_kendaraan, dt_temp_kode_wilayah

        try:
            dt_temp_no_uji = dt_temp_no_uji_new = dt_temp_no_wilayah = dt_temp_no_kendaraan = dt_temp_no_plat = dt_temp_no_pol = ""
            dt_temp_nama = dt_temp_no_hp = dt_temp_alamat = dt_temp_id_izin = dt_temp_wilayah = dt_temp_provinsi = dt_temp_kabupaten_kota = dt_temp_kecamatan = ""
            dt_temp_id_merk = dt_temp_id_subjenis = dt_temp_type = dt_temp_tahun_buat = dt_temp_silinder = dt_temp_warna = dt_temp_chasis = dt_temp_mesin = dt_temp_warna_plat = ""
            dt_temp_bhn_bkr = dt_temp_jbb = dt_temp_daya_motor = dt_temp_tgl_uji_terakhir = dt_temp_tgl_uji_habis = dt_temp_status_uji = dt_temp_status_penerbitan = dt_temp_jenis_kendaraan = dt_temp_kode_jenis_kendaraan = dt_temp_kode_wilayah = ""

            self.ids.tx_nopol.text = "" 
            self.ids.tx_nouji.text = "" 
            self.ids.lb_temp_nama.text = self.ids.lb_temp_alamat.text = ""
            self.ids.lb_temp_no_uji.text = self.ids.lb_temp_no_pol.text = self.ids.lb_temp_status_uji.text = self.ids.lb_temp_tgl_uji_terakhir.text = self.ids.lb_temp_tgl_uji_habis.text = ""
            self.ids.lb_temp_merk.text = self.ids.lb_temp_type.text = self.ids.lb_temp_jenis_kendaraan.text = self.ids.lb_temp_warna.text = ""
            self.ids.lb_temp_chasis.text = self.ids.lb_temp_mesin.text = self.ids.lb_temp_bahan_bakar.text = self.ids.lb_temp_jbb.text = ""
            self.ids.bt_register.disabled = True

            self.exec_navigate_main()
            
        except Exception as e:
            toast_msg = f'Gagal Memuat Data'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}") 

    def exec_find(self):
        global mydb, db_users, db_merk, db_bahan_bakar, db_warna
        global dt_id_user, dt_user, dt_foto_user
        global dt_temp_no_uji, dt_temp_no_uji_new, dt_temp_no_wilayah, dt_temp_no_kendaraan, dt_temp_no_plat, dt_temp_no_pol
        global dt_temp_nama, dt_temp_no_hp, dt_temp_alamat, dt_temp_id_izin, dt_temp_wilayah, dt_temp_provinsi, dt_temp_kabupaten_kota, dt_temp_kecamatan
        global dt_temp_id_merk, dt_temp_id_subjenis, dt_temp_type, dt_temp_tahun_buat, dt_temp_silinder, dt_temp_warna, dt_temp_chasis, dt_temp_mesin, dt_temp_warna_plat
        global dt_temp_bhn_bkr, dt_temp_jbb, dt_temp_daya_motor, dt_temp_tgl_uji_terakhir, dt_temp_tgl_uji_habis, dt_temp_status_uji, dt_temp_status_penerbitan, dt_temp_jenis_kendaraan, dt_temp_kode_jenis_kendaraan, dt_temp_kode_wilayah

        try:
            dt_find_no_pol = self.ids.tx_nopol.text
            dt_find_no_uji = self.ids.tx_nouji.text
            self.exec_fetch_master_data(dt_find_no_pol, dt_find_no_uji)

            self.ids.lb_temp_nama.text = f'{dt_temp_nama}'
            self.ids.lb_temp_alamat.text = f'{dt_temp_alamat}'
            self.ids.lb_temp_no_uji.text = f'{dt_temp_no_uji}'
            self.ids.lb_temp_no_pol.text = f'{dt_temp_no_pol}'
            self.ids.lb_temp_status_uji.text = 'Berkala' if dt_temp_status_uji == 'B' else 'Uji Ulang' if dt_temp_status_uji == 'U' else 'Baru' if dt_temp_status_uji == 'BR' else 'Numpang Uji' if dt_temp_status_uji == 'NB' else 'Mutasi'
            self.ids.lb_temp_tgl_uji_terakhir.text = f'{dt_temp_tgl_uji_terakhir}'
            self.ids.lb_temp_tgl_uji_habis.text = f'{dt_temp_tgl_uji_habis}'
            self.ids.lb_temp_merk.text = '-' if dt_temp_id_merk == None else f"{db_merk[np.where(db_merk == dt_temp_id_merk)[0][0],1]}"
            self.ids.lb_temp_type.text = f'{dt_temp_type}'
            self.ids.lb_temp_jenis_kendaraan.text = f'{dt_temp_jenis_kendaraan}'
            self.ids.lb_temp_warna.text = '-' if dt_temp_warna == None else f"{db_warna[np.where(db_warna == dt_temp_warna)[0][0],1]}"
            self.ids.lb_temp_chasis.text = f'{dt_temp_chasis}'
            self.ids.lb_temp_mesin.text = f'{dt_temp_mesin}'
            self.ids.lb_temp_bahan_bakar.text = '-' if dt_temp_bhn_bkr == None else f"{db_bahan_bakar[np.where(db_bahan_bakar == dt_temp_bhn_bkr)[0][0],1]}"
            self.ids.lb_temp_jbb.text = f'{dt_temp_jbb}'
            self.ids.lb_temp_berat_kosong.text = f'{dt_temp_brt_ksg}'
            self.ids.bt_register.disabled = False
            
        except Exception as e:
            toast_msg = f'Gagal Menemukan Data, Silahkan Isi Nomor Uji atau Nomor Polisi dengan Benar'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}") 

    def exec_fetch_master_data(self, dt_find_no_pol, dt_find_no_uji):
        global mydb, db_users, db_merk, db_bahan_bakar, db_warna
        global dt_id_user, dt_user, dt_foto_user
        global dt_temp_no_uji, dt_temp_no_uji_new, dt_temp_no_wilayah, dt_temp_no_kendaraan, dt_temp_no_plat, dt_temp_no_pol
        global dt_temp_nama, dt_temp_no_hp, dt_temp_alamat, dt_temp_id_izin, dt_temp_wilayah, dt_temp_provinsi, dt_temp_kabupaten_kota, dt_temp_kecamatan
        global dt_temp_id_merk, dt_temp_id_subjenis, dt_temp_type, dt_temp_tahun_buat, dt_temp_silinder, dt_temp_warna, dt_temp_chasis, dt_temp_mesin, dt_temp_warna_plat
        global dt_temp_bhn_bkr, dt_temp_jbb, dt_temp_brt_ksg, dt_temp_daya_motor, dt_temp_tgl_uji_terakhir, dt_temp_tgl_uji_habis, dt_temp_status_uji, dt_temp_status_penerbitan, dt_temp_jenis_kendaraan, dt_temp_kode_jenis_kendaraan, dt_temp_kode_wilayah

        try:
            mycursor = mydb.cursor()
            if dt_find_no_pol != "" and dt_find_no_uji == "":
                mycursor.execute(f"SELECT NOUJI, NEW_NOUJI, NOWIL, NOKDR, PLAT, NOPOL, NAMA, NOHP, ALAMAT, ID_IZIN, WLY, PROP, KABKOT, KEC, MERK_ID, idjeniskendaraan, TYPE, TH_BUAT, SILINDER, WARNA_KEND, CHASIS, MESIN, WARNA_PLAT, BHN_BAKAR, JBB, BERATKOSONG, DAYAMOTOR, TGL_UJI_TERAKHIR, STATUSUJI, statuspenerbitan, idjeniskendaraan, kd_jnskendaraan, kodewilayah FROM {TB_DATA_MASTER} WHERE NOPOL = '{dt_find_no_pol}' ")
            elif dt_find_no_uji != "":
                mycursor.execute(f"SELECT NOUJI, NEW_NOUJI, NOWIL, NOKDR, PLAT, NOPOL, NAMA, NOHP, ALAMAT, ID_IZIN, WLY, PROP, KABKOT, KEC, MERK_ID, idjeniskendaraan, TYPE, TH_BUAT, SILINDER, WARNA_KEND, CHASIS, MESIN, WARNA_PLAT, BHN_BAKAR, JBB, BERATKOSONG, DAYAMOTOR, TGL_UJI_TERAKHIR, STATUSUJI, statuspenerbitan, idjeniskendaraan, kd_jnskendaraan, kodewilayah FROM {TB_DATA_MASTER} WHERE NOUJI = '{dt_find_no_uji}' ")
            elif dt_find_no_uji == "" and dt_find_no_pol == "":
                toast("Silahkan Isi Nomor Uji atau Nomor Polisi dengan Benar")
            myresult = mycursor.fetchone()
            mydb.commit()
            db_master_data = np.array(myresult).T

            if myresult is None:
                toast('Data Tidak Ditemukan di Database, Silahkan Ajukan Pengujian Baru')
                self.exec_cancel()
            else:
                dt_temp_no_uji = db_master_data[0]
                dt_temp_no_uji_new = db_master_data[1]
                dt_temp_no_wilayah = db_master_data[2]
                dt_temp_no_kendaraan = db_master_data[3]
                dt_temp_no_plat = db_master_data[4]
                dt_temp_no_pol = db_master_data[5]
                dt_temp_nama = db_master_data[6]
                dt_temp_no_hp = db_master_data[7]
                dt_temp_alamat = db_master_data[8]
                dt_temp_id_izin = db_master_data[9]
                dt_temp_wilayah = db_master_data[10]
                dt_temp_provinsi = db_master_data[11]
                dt_temp_kabupaten_kota = db_master_data[12]
                dt_temp_kecamatan = db_master_data[13]
                dt_temp_id_merk = db_master_data[14]
                dt_temp_id_subjenis = db_master_data[15]
                dt_temp_type = db_master_data[16]
                dt_temp_tahun_buat = db_master_data[17]
                dt_temp_silinder = db_master_data[18]
                dt_temp_warna = db_master_data[19]
                dt_temp_chasis = db_master_data[20]
                dt_temp_mesin = db_master_data[21]
                dt_temp_warna_plat = db_master_data[22]
                dt_temp_bhn_bkr = db_master_data[23]
                dt_temp_jbb = db_master_data[24]
                dt_temp_brt_ksg = db_master_data[25]
                dt_temp_daya_motor = db_master_data[26]
                
                dt_temp_status_uji = db_master_data[28]
                dt_temp_status_penerbitan = db_master_data[29]
                dt_temp_jenis_kendaraan = db_master_data[30]
                dt_temp_kode_jenis_kendaraan = db_master_data[31]
                dt_temp_kode_wilayah = db_master_data[32]

                if(db_master_data[26] is not None):
                    last_uji_date = db_master_data[27]
                else:
                    last_uji_date = datetime.datetime(1900, 1, 1)

                if(last_uji_date.month <= 6):
                    year_replaced = last_uji_date.year
                    month_replaced = last_uji_date.month + 6
                    day_replaced = last_uji_date.day
                else:
                    year_replaced = last_uji_date.year + 1
                    month_replaced = last_uji_date.month - 6
                    day_replaced = last_uji_date.day
                
                if(last_uji_date.day > 29):
                    if month_replaced == 2:
                        day_replaced = 29
                    if month_replaced == 4 or month_replaced == 6 or month_replaced == 9 or month_replaced == 11:
                        day_replaced = 30
                    
                dt_temp_tgl_uji_terakhir = str(last_uji_date.strftime('%d-%m-%Y'))
                dt_temp_tgl_uji_habis = str(last_uji_date.replace(month=month_replaced, year=year_replaced, day=day_replaced).strftime('%d-%m-%Y'))
                
        except Exception as e:
            toast_msg = f'Gagal Menemukan Data dari Database Master'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}") 

    def exec_register(self):
        global mydb, db_users, db_merk, db_bahan_bakar, db_warna
        global dt_id_user, dt_user, dt_foto_user
        global dt_temp_no_uji, dt_temp_no_uji_new, dt_temp_no_wilayah, dt_temp_no_kendaraan, dt_temp_no_plat, dt_temp_no_pol
        global dt_temp_nama, dt_temp_no_hp, dt_temp_alamat, dt_temp_id_izin, dt_temp_wilayah, dt_temp_provinsi, dt_temp_kabupaten_kota, dt_temp_kecamatan
        global dt_temp_id_merk, dt_temp_id_subjenis, dt_temp_type, dt_temp_tahun_buat, dt_temp_silinder, dt_temp_warna, dt_temp_chasis, dt_temp_mesin, dt_temp_warna_plat
        global dt_temp_bhn_bkr, dt_temp_jbb, dt_temp_brt_ksg, dt_temp_daya_motor, dt_temp_tgl_uji_terakhir, dt_temp_tgl_uji_habis, dt_temp_status_uji, dt_temp_status_penerbitan, dt_temp_jenis_kendaraan, dt_temp_kode_jenis_kendaraan, dt_temp_kode_wilayah

        try:
            mycursor = mydb.cursor()
            mycursor.execute(f"SELECT MAX(noantrian) FROM {TB_DATA}")
            result = mycursor.fetchone()
            last_noantrian = int(result[0]) if result[0] is not None else 0
            noantrian = f"{last_noantrian + 1:04d}"

            mycursor = mydb.cursor()
            sql = f"INSERT INTO {TB_DATA} (noantrian, nopol, nouji, NEW_NOUJI, merk, type, idjeniskendaraan, jbb, berat_kosong, warna) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            values = (noantrian, dt_temp_no_pol, dt_temp_no_uji, dt_temp_no_uji_new, dt_temp_id_merk, dt_temp_type, dt_temp_id_subjenis, dt_temp_jbb, dt_temp_brt_ksg, dt_temp_warna)
            mycursor.execute(sql, values)
            mydb.commit()

        except Exception as e:
            toast_msg = f'Gagal menambah data antrian baru'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}") 

        self.exec_cancel()

    def exec_navigate_home(self):
        try:
            self.screen_manager.current = 'screen_home'

        except Exception as e:
            toast_msg = f'Gagal Berpindah ke Halaman Awal'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}") 

    def exec_navigate_login(self):
        global dt_user
        try:
            if (dt_user == ""):
                self.screen_manager.current = 'screen_login'
            else:
                toast(f"Anda sudah login sebagai {dt_user}")

        except Exception as e:
            toast_msg = f'Gagal Berpindah ke Halaman Login'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}") 

    def exec_navigate_main(self):
        try:
            self.screen_manager.current = 'screen_main'

        except Exception as e:
            toast_msg = f'Gagal Berpindah ke Halaman Utama'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}") 

class ScreenMenu(MDScreen):        
    def __init__(self, **kwargs):
        super(ScreenMenu, self).__init__(**kwargs)
        Clock.schedule_once(self.delayed_init, 1)        

    def delayed_init(self, dt):
        self.ids.lb_title.text = APP_TITLE
        self.ids.lb_subtitle.text = APP_SUBTITLE        
        self.ids.img_pemkab.source = f'assets/images/{IMG_LOGO_PEMKAB}'
        self.ids.img_dishub.source = f'assets/images/{IMG_LOGO_DISHUB}'
        self.ids.lb_pemkab.text = LB_PEMKAB
        self.ids.lb_dishub.text = LB_DISHUB
        self.ids.lb_unit.text = LB_UNIT
        self.ids.lb_unit_address.text = LB_UNIT_ADDRESS

    def on_enter(self):
        global db_merk, db_bahan_bakar, db_warna
        global dt_no_antri, dt_no_pol, dt_no_uji, dt_sts_uji
        global dt_merk, dt_type, dt_jns_kend, dt_jbb, dt_brt_ksg, dt_bhn_bkr, dt_warna, dt_load_flag, dt_brake_flag, dt_handbrake_flag

        self.ids.lb_no_antri.text = str(dt_no_antri)
        self.ids.lb_no_pol.text = str(dt_no_pol)
        self.ids.lb_no_uji.text = str(dt_no_uji)
        self.ids.lb_sts_uji.text = 'Berkala' if dt_sts_uji == 'B' else 'Uji Ulang' if dt_sts_uji == 'U' else 'Baru' if dt_sts_uji == 'BR' else 'Numpang Uji' if dt_sts_uji == 'NB' else 'Mutasi'
        self.ids.lb_merk.text = '-' if dt_merk == None else f"{db_merk[np.where(db_merk == dt_merk)[0][0],1]}"
        self.ids.lb_type.text = str(dt_type)
        self.ids.lb_jns_kend.text = str(dt_jns_kend)
        self.ids.lb_jbb.text = str(dt_jbb)
        self.ids.lb_brt_ksg.text = str(dt_brt_ksg)
        self.ids.lb_bhn_bkr.text = '-' if dt_bhn_bkr == None else f"{db_bahan_bakar[np.where(db_bahan_bakar == dt_bhn_bkr)[0][0],1]}"
        self.ids.lb_warna.text = '-' if dt_warna == None else f"{db_warna[np.where(db_warna == dt_warna)[0][0],1]}"

    def exec_select_axle(self, number):
        global dt_test_number

        dt_test_number = number - 1

    def exec_start_load(self):
        self.open_screen_load_meter()

    def exec_start_brake(self):
        self.open_screen_brake_meter()

    def exec_start_handbrake(self):
        self.open_screen_handbrake_meter()

    def exec_navigate_main(self):
        try:
            self.screen_manager.current = 'screen_main'

        except Exception as e:
            toast_msg = f'Terjadi kesalahan saat berpindah ke halaman Utama'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

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
        Clock.schedule_once(self.delayed_init, 1)        

    def delayed_init(self, dt):
        self.ids.lb_title.text = APP_TITLE
        self.ids.lb_subtitle.text = APP_SUBTITLE        
        self.ids.img_pemkab.source = f'assets/images/{IMG_LOGO_PEMKAB}'
        self.ids.img_dishub.source = f'assets/images/{IMG_LOGO_DISHUB}'
        self.ids.lb_pemkab.text = LB_PEMKAB
        self.ids.lb_dishub.text = LB_DISHUB
        self.ids.lb_unit.text = LB_UNIT
        self.ids.lb_unit_address.text = LB_UNIT_ADDRESS

    def on_enter(self):
        global db_merk, db_bahan_bakar, db_warna
        global dt_no_antri, dt_no_pol, dt_no_uji, dt_sts_uji
        global dt_merk, dt_type, dt_jns_kend, dt_jbb, dt_brt_ksg, dt_bhn_bkr, dt_warna, dt_load_flag, dt_brake_flag, dt_handbrake_flag

        self.ids.lb_no_antri.text = str(dt_no_antri)
        self.ids.lb_no_pol.text = str(dt_no_pol)
        self.ids.lb_no_uji.text = str(dt_no_uji)
        self.ids.lb_sts_uji.text = 'Berkala' if dt_sts_uji == 'B' else 'Uji Ulang' if dt_sts_uji == 'U' else 'Baru' if dt_sts_uji == 'BR' else 'Numpang Uji' if dt_sts_uji == 'NB' else 'Mutasi'
        self.ids.lb_merk.text = '-' if dt_merk == None else f"{db_merk[np.where(db_merk == dt_merk)[0][0],1]}"
        self.ids.lb_type.text = str(dt_type)
        self.ids.lb_jns_kend.text = str(dt_jns_kend)
        self.ids.lb_jbb.text = str(dt_jbb)
        self.ids.lb_brt_ksg.text = str(dt_brt_ksg)
        self.ids.lb_bhn_bkr.text = '-' if dt_bhn_bkr == None else f"{db_bahan_bakar[np.where(db_bahan_bakar == dt_bhn_bkr)[0][0],1]}"
        self.ids.lb_warna.text = '-' if dt_warna == None else f"{db_warna[np.where(db_warna == dt_warna)[0][0],1]}"
        self.exec_reload()

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
        Clock.schedule_once(self.delayed_init, 1)
        
    def delayed_init(self, dt):
        self.ids.lb_title.text = APP_TITLE
        self.ids.lb_subtitle.text = APP_SUBTITLE        
        self.ids.img_pemkab.source = f'assets/images/{IMG_LOGO_PEMKAB}'
        self.ids.img_dishub.source = f'assets/images/{IMG_LOGO_DISHUB}'
        self.ids.lb_pemkab.text = LB_PEMKAB
        self.ids.lb_dishub.text = LB_DISHUB
        self.ids.lb_unit.text = LB_UNIT
        self.ids.lb_unit_address.text = LB_UNIT_ADDRESS

    def on_enter(self):
        global db_merk, db_bahan_bakar, db_warna
        global dt_no_antri, dt_no_pol, dt_no_uji, dt_sts_uji
        global dt_merk, dt_type, dt_jns_kend, dt_jbb, dt_brt_ksg, dt_bhn_bkr, dt_warna, dt_load_flag, dt_brake_flag, dt_handbrake_flag

        self.ids.lb_no_antri.text = str(dt_no_antri)
        self.ids.lb_no_pol.text = str(dt_no_pol)
        self.ids.lb_no_uji.text = str(dt_no_uji)
        self.ids.lb_sts_uji.text = 'Berkala' if dt_sts_uji == 'B' else 'Uji Ulang' if dt_sts_uji == 'U' else 'Baru' if dt_sts_uji == 'BR' else 'Numpang Uji' if dt_sts_uji == 'NB' else 'Mutasi'
        self.ids.lb_merk.text = '-' if dt_merk == None else f"{db_merk[np.where(db_merk == dt_merk)[0][0],1]}"
        self.ids.lb_type.text = str(dt_type)
        self.ids.lb_jns_kend.text = str(dt_jns_kend)
        self.ids.lb_jbb.text = str(dt_jbb)
        self.ids.lb_brt_ksg.text = str(dt_brt_ksg)
        self.ids.lb_bhn_bkr.text = '-' if dt_bhn_bkr == None else f"{db_bahan_bakar[np.where(db_bahan_bakar == dt_bhn_bkr)[0][0],1]}"
        self.ids.lb_warna.text = '-' if dt_warna == None else f"{db_warna[np.where(db_warna == dt_warna)[0][0],1]}"

    def exec_motor_brake_on(self):
        global flag_conn_stat
        global flag_motor_brake
        
        flag_motor_brake = True
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_coil(3075, True, slave=1) #M3
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send exec_motor_brake_on data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def rel_motor_brake_on(self):
        global flag_conn_stat
        global flag_motor_brake

        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_coil(3075, False, slave=1) #M3
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send rel_motor_brake_on data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_motor_brake_off(self):
        global flag_conn_stat
        global flag_motor_brake

        flag_motor_brake = False
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_coil(3076, True, slave=1) #M4
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send exec_motor_brake_off data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def rel_motor_brake_off(self):
        global flag_conn_stat
        global flag_motor_brake

        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_coil(3076, False, slave=1) #M4
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send rel_motor_brake_on data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

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
        Clock.schedule_once(self.delayed_init, 1)
        
    def delayed_init(self, dt):
        self.ids.lb_title.text = APP_TITLE
        self.ids.lb_subtitle.text = APP_SUBTITLE        
        self.ids.img_pemkab.source = f'assets/images/{IMG_LOGO_PEMKAB}'
        self.ids.img_dishub.source = f'assets/images/{IMG_LOGO_DISHUB}'
        self.ids.lb_pemkab.text = LB_PEMKAB
        self.ids.lb_dishub.text = LB_DISHUB
        self.ids.lb_unit.text = LB_UNIT
        self.ids.lb_unit_address.text = LB_UNIT_ADDRESS

    def on_enter(self):
        global db_merk, db_bahan_bakar, db_warna
        global dt_no_antri, dt_no_pol, dt_no_uji, dt_sts_uji
        global dt_merk, dt_type, dt_jns_kend, dt_jbb, dt_brt_ksg, dt_bhn_bkr, dt_warna, dt_load_flag, dt_brake_flag, dt_handbrake_flag

        self.ids.lb_no_antri.text = str(dt_no_antri)
        self.ids.lb_no_pol.text = str(dt_no_pol)
        self.ids.lb_no_uji.text = str(dt_no_uji)
        self.ids.lb_sts_uji.text = 'Berkala' if dt_sts_uji == 'B' else 'Uji Ulang' if dt_sts_uji == 'U' else 'Baru' if dt_sts_uji == 'BR' else 'Numpang Uji' if dt_sts_uji == 'NB' else 'Mutasi'
        self.ids.lb_merk.text = '-' if dt_merk == None else f"{db_merk[np.where(db_merk == dt_merk)[0][0],1]}"
        self.ids.lb_type.text = str(dt_type)
        self.ids.lb_jns_kend.text = str(dt_jns_kend)
        self.ids.lb_jbb.text = str(dt_jbb)
        self.ids.lb_brt_ksg.text = str(dt_brt_ksg)
        self.ids.lb_bhn_bkr.text = '-' if dt_bhn_bkr == None else f"{db_bahan_bakar[np.where(db_bahan_bakar == dt_bhn_bkr)[0][0],1]}"
        self.ids.lb_warna.text = '-' if dt_warna == None else f"{db_warna[np.where(db_warna == dt_warna)[0][0],1]}"

    def exec_motor_brake_on(self):
        global flag_conn_stat
        global flag_motor_brake
        
        flag_motor_brake = True
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_coil(3075, True, slave=1) #M3
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send exec_motor_brake_on data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def rel_motor_brake_on(self):
        global flag_conn_stat
        global flag_motor_brake

        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_coil(3075, False, slave=1) #M3
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send rel_motor_brake_on data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_motor_brake_off(self):
        global flag_conn_stat
        global flag_motor_brake

        flag_motor_brake = False
        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_coil(3076, True, slave=1) #M4
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send exec_motor_brake_off data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def rel_motor_brake_off(self):
        global flag_conn_stat
        global flag_motor_brake

        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_coil(3076, False, slave=1) #M4
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send rel_motor_brake_on data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

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
        self.ids.lb_handbrake_l_val.text = "..."
        self.ids.lb_handbrake_r_val.text = " "

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
        Clock.schedule_once(self.delayed_init, 1)        

    def delayed_init(self, dt):
        self.ids.lb_title.text = APP_TITLE
        self.ids.lb_subtitle.text = APP_SUBTITLE        
        self.ids.img_pemkab.source = f'assets/images/{IMG_LOGO_PEMKAB}'
        self.ids.img_dishub.source = f'assets/images/{IMG_LOGO_DISHUB}'
        self.ids.lb_pemkab.text = LB_PEMKAB
        self.ids.lb_dishub.text = LB_DISHUB
        self.ids.lb_unit.text = LB_UNIT
        self.ids.lb_unit_address.text = LB_UNIT_ADDRESS

    def on_enter(self):
        global db_merk, db_bahan_bakar, db_warna
        global dt_user, dt_no_antri, dt_no_pol, dt_no_uji, dt_nama, dt_jns_kend
        global dt_load_flag, db_load_left_value, db_load_right_value, db_load_total_value, db_load_flag, dt_id_user
        global dt_brake_flag, db_brake_left_value, db_brake_right_value, db_brake_total_value, db_brake_difference_value, db_brake_flag
        global dt_handbrake_flag, db_handbrake_left_value, db_handbrake_right_value, db_handbrake_total_value, db_handbrake_difference_value, db_handbrake_flag
        global dt_load_total_value, dt_brake_total_value, dt_brake_efficiency_value, dt_brake_difference_value, dt_handbrake_total_value, dt_handbrake_efficiency_value, dt_handbrake_difference_value
        global dt_test_number

        self.exec_reload_table_detail()
        try:
            if(dt_brake_efficiency_value >= STANDARD_MIN_EFFICIENCY_BRAKE):
                dt_brake_flag = 2            
            else:
                dt_brake_flag = 1
            
            if(dt_handbrake_efficiency_value >= STANDARD_MIN_EFFICIENCY_HANDBRAKE):
                dt_handbrake_flag = 2
            else:
                dt_handbrake_flag = 1

            dt_brake_resume_flag = all(x == 2 for x in db_brake_flag if x != 0)
            if(dt_brake_resume_flag and int(dt_brake_flag) == 2 and int(dt_handbrake_flag) == 2):
                self.ids.lb_test_result.md_bg_color = colors['Green']['200']
                self.ids.lb_test_result.text_color = colors['Green']['700']
                self.ids.lb_test_result.text = f"LULUS"
            else:
                self.ids.lb_test_result.md_bg_color = colors['Red']['A200']
                self.ids.lb_test_result.text_color = colors['Red']['A700']
                self.ids.lb_test_result.text = f"TIDAK LULUS"

            self.ids.lb_load_left_sum.text = f'{int(np.sum(db_load_left_value))} kg'
            self.ids.lb_load_right_sum.text = f'{int(np.sum(db_load_right_value))} kg'
            self.ids.lb_load_total_sum.text = f'{int(dt_load_total_value)} kg'

            self.ids.lb_brake_left_sum.text = f'{int(np.sum(db_brake_left_value))} kg'
            self.ids.lb_brake_right_sum.text = f'{int(np.sum(db_brake_right_value))} kg'
            self.ids.lb_brake_total_sum.text = f'{int(dt_brake_total_value)} kg'
            self.ids.lb_brake_efficiency.text = f'{np.round(dt_brake_efficiency_value, 1)} %'
            self.ids.lb_brake_status.text = f'Lulus' if int(dt_brake_flag) == 2 else 'Tidak Lulus' if int(dt_brake_flag) == 1 else 'Belum Diuji'

            self.ids.lb_handbrake_left_sum.text = f'{int(np.sum(db_handbrake_left_value))} kg'
            self.ids.lb_handbrake_right_sum.text = f'{int(np.sum(db_handbrake_right_value))} kg'
            self.ids.lb_handbrake_total_sum.text = f'{int(dt_handbrake_total_value)} kg'
            self.ids.lb_handbrake_efficiency.text = f'{np.round(dt_handbrake_efficiency_value, 1)} %'
            self.ids.lb_handbrake_status.text = f'Lulus' if int(dt_handbrake_flag) == 2 else 'Tidak Lulus' if int(dt_handbrake_flag) == 1 else 'Belum Diuji'

            Logger.info(f"Status: Load:{dt_load_flag}, Brake:{dt_brake_flag}, Handbrake{dt_handbrake_flag}")

        except Exception as e:
            toast_msg = f'Error Create Resume: {e}'
            Logger.error(f"{self.name}: {toast_msg}, {e}")   


    def exec_reload_table_detail(self):
        global dt_user, dt_no_antri, dt_no_pol, dt_no_uji, dt_nama, dt_jns_kend
        global dt_load_flag, db_load_left_value, db_load_right_value, db_load_total_value, dt_id_user
        global dt_brake_flag, db_brake_left_value, db_brake_right_value, db_brake_total_value, db_brake_difference_value, db_brake_flag
        global dt_handbrake_flag, db_handbrake_left_value, db_handbrake_right_value, db_handbrake_total_value, db_handbrake_difference_value, db_handbrake_flag
        global dt_load_total_value, dt_brake_total_value, dt_brake_efficiency_value, dt_brake_difference_value, dt_handbrake_total_value, dt_handbrake_efficiency_value, dt_handbrake_difference_value
        global dt_test_number

        try:            
            layout_list_load = self.ids.layout_list_load
            layout_list_load.clear_widgets(children=None)
            layout_list_brake = self.ids.layout_list_brake
            layout_list_brake.clear_widgets(children=None)
            layout_list_handbrake = self.ids.layout_list_handbrake
            layout_list_handbrake.clear_widgets(children=None)
        except Exception as e:
            toast_msg = f'Error Remove Widget: {e}'
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

        try: 
            layout_list_load = self.ids.layout_list_load
            for i in range(10):
                if (db_load_total_value[i] > 0.0):
                    layout_list_load.add_widget(
                        MDCard(
                            MDLabel(text=f"Sumbu {i+1}", size_hint_x= 0.2),
                            MDLabel(text=f"{db_load_left_value[i]}", size_hint_x= 0.2),
                            MDLabel(text=f"{db_load_right_value[i]}", size_hint_x= 0.2),
                            MDLabel(text=f"{db_load_total_value[i]}", size_hint_x= 0.2),
                            padding = 20,
                            size_hint_y=None,
                            height=dp(int(60 * 800 / window_size_y)),                          
                            )
                        )
        except Exception as e:
            toast_msg = f'Error Reload Load Table: {e}'
            Logger.error(f"{self.name}: {toast_msg}, {e}")          

        try:           
            layout_list_brake = self.ids.layout_list_brake
            for i in range(10):
                if (db_brake_total_value[i] > 0.0):
                    layout_list_brake.add_widget(
                        MDCard(
                            MDLabel(text=f"Sumbu {i+1}", size_hint_x= 0.16),
                            MDLabel(text=f"{db_brake_left_value[i]}", size_hint_x= 0.16),
                            MDLabel(text=f"{db_brake_right_value[i]}", size_hint_x= 0.16),
                            MDLabel(text=f"{db_brake_total_value[i]}", size_hint_x= 0.16),
                            MDLabel(text=f"{db_brake_difference_value[i]}", size_hint_x= 0.16),
                            MDLabel(text=f"Lulus" if int(db_brake_flag[i]) == 2 else "Tidak Lulus" if int(db_brake_flag[i]) == 1 else "Belum Diuji", size_hint_x= 0.16),
                            padding = 20,
                            size_hint_y=None,
                            height=dp(int(60 * 800 / window_size_y)),
                            )
                        )
        except Exception as e:
            toast_msg = f'Error Reload Brake Table: {e}'
            Logger.error(f"{self.name}: {toast_msg}, {e}")

        try:           
            layout_list_handbrake = self.ids.layout_list_handbrake
            for i in range(10):
                if (db_handbrake_total_value[i] > 0.0):
                    layout_list_handbrake.add_widget(
                        MDCard(
                            MDLabel(text=f"Sumbu {i+1}", size_hint_x= 0.2),
                            MDLabel(text=f"{db_handbrake_left_value[i]}", size_hint_x= 0.2),
                            MDLabel(text=f"{db_handbrake_right_value[i]}", size_hint_x= 0.2),
                            MDLabel(text=f"{db_handbrake_total_value[i]}", size_hint_x= 0.2),
                            padding = 20,
                            size_hint_y=None,
                            height=dp(int(60 * 800 / window_size_y)),
                            )
                        )
        except Exception as e:
            toast_msg = f'Error Reload Brake Table: {e}'
            Logger.error(f"{self.name}: {toast_msg}, {e}")

    def exec_navigate_back(self):
        try:
            self.screen_manager.current = 'screen_menu'

        except Exception as e:
            toast_msg = f'Error Navigate to Menu Screen: {e}'
            toast(toast_msg)   
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_save(self):
        global flag_play
        global count_starting, count_get_data
        global mydb, db_antrian
        global db_load_left_value, db_load_right_value, db_load_total_value, db_load_flag, dt_id_user, dt_no_antri
        global db_brake_left_value, db_brake_right_value, db_brake_total_value, db_brake_difference_value, db_brake_flag
        global db_handbrake_left_value, db_handbrake_right_value, db_handbrake_total_value, db_handbrake_difference_value, db_handbrake_flag
        global dt_load_total_value, dt_brake_total_value, dt_brake_efficiency_value, dt_brake_difference_value, dt_handbrake_total_value, dt_handbrake_efficiency_value, dt_handbrake_difference_value
        global dt_test_number

        try:
            try:
                mycursor = mydb.cursor()
                # Build SQL query safely
                sql1 = f"UPDATE {TB_DATA} SET load_flag = %s"
                sql2 = (", load_l_s1_value = %s, load_l_s2_value = %s, load_l_s3_value = %s, "
                        "load_l_s4_value = %s, load_l_s5_value = %s, load_l_s6_value = %s, "
                        "load_l_s7_value = %s, load_l_s8_value = %s, load_l_s9_value = %s, "
                        "load_l_s10_value = %s, load_l_s11_value = %s, load_l_s12_value = %s")
                sql3 = (", load_r_s1_value = %s, load_r_s2_value = %s, load_r_s3_value = %s, "
                        "load_r_s4_value = %s, load_r_s5_value = %s, load_r_s6_value = %s, "
                        "load_r_s7_value = %s, load_r_s8_value = %s, load_r_s9_value = %s, "
                        "load_r_s10_value = %s, load_r_s11_value = %s, load_r_s12_value = %s")
                sql4 = ", load_total_value = %s, load_user = %s, load_post = %s WHERE noantrian = %s"
                sql = sql1 + sql2 + sql3 + sql4

                # Prepare values
                sql_load_flag = dt_load_flag
                dt_load_post = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())

                # Ensure these are tuples/lists of length 12
                assert len(db_load_left_value) == 12, "db_load_left_value must have 12 elements"
                assert len(db_load_right_value) == 12, "db_load_right_value must have 12 elements"

                # Build parameter tuple
                sql_val = (
                    sql_load_flag,                         # 1
                    *db_load_left_value,                   # 12
                    *db_load_right_value,                  # 12
                    dt_load_total_value,                   # 1
                    dt_id_user,                            # 1
                    dt_load_post,                          # 1
                    dt_no_antri                            # 1
                )

                # Total parameters: 1 + 12 + 12 + 1 + 1 + 1 + 1 = 29
                expected_params = 29
                if len(sql_val) != expected_params:
                    Logger.error(f"SQL Value count mismatch: expected {expected_params}, got {len(sql_val)}")
                else:
                    mycursor.execute(sql, sql_val)
                    mydb.commit()
                    Logger.info(f"Successfully updated load data for noantrian={dt_no_antri}")
            except Exception as e:
                toast_msg = f'Error Save Load Data'
                toast(toast_msg)
                Logger.error(f"{self.name}: {toast_msg}, {e}")  

            try:
                mycursor = mydb.cursor()
                # Build SQL query safely
                sql1 = f"UPDATE {TB_DATA} SET brake_flag = %s"
                sql2 = (
                    ", brake_l_s1_value = %s, brake_l_s2_value = %s, brake_l_s3_value = %s, "
                    "brake_l_s4_value = %s, brake_l_s5_value = %s, brake_l_s6_value = %s, "
                    "brake_l_s7_value = %s, brake_l_s8_value = %s, brake_l_s9_value = %s, "
                    "brake_l_s10_value = %s, brake_l_s11_value = %s, brake_l_s12_value = %s"
                )
                sql3 = (
                    ", brake_r_s1_value = %s, brake_r_s2_value = %s, brake_r_s3_value = %s, "
                    "brake_r_s4_value = %s, brake_r_s5_value = %s, brake_r_s6_value = %s, "
                    "brake_r_s7_value = %s, brake_r_s8_value = %s, brake_r_s9_value = %s, "
                    "brake_r_s10_value = %s, brake_r_s11_value = %s, brake_r_s12_value = %s"
                )
                sql4 = (
                    ", brake_difference_s1_value = %s, brake_difference_s2_value = %s, brake_difference_s3_value = %s, "
                    "brake_difference_s4_value = %s, brake_difference_s5_value = %s, brake_difference_s6_value = %s, "
                    "brake_difference_s7_value = %s, brake_difference_s8_value = %s, brake_difference_s9_value = %s, "
                    "brake_difference_s10_value = %s, brake_difference_s11_value = %s, brake_difference_s12_value = %s"
                )
                sql5 = ", brake_total_value = %s, brake_efficiency_value = %s, brake_user = %s, brake_post = %s WHERE noantrian = %s"
                sql = sql1 + sql2 + sql3 + sql4 + sql5

                sql_brake_flag = dt_brake_flag
                dt_brake_post = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())

                expected_len = 12
                arrays = {
                    'db_brake_left_value': db_brake_left_value,
                    'db_brake_right_value': db_brake_right_value,
                    'db_brake_difference_value': db_brake_difference_value,
                }

                for name, arr in arrays.items():
                    if not isinstance(arr, (list, tuple)) or len(arr) != expected_len:
                        Logger.error(f"{self.screen_manager.current}: {name} must be a list/tuple of 12 values. Got: {arr}")
                        raise ValueError(f"{name} must have exactly 12 elements")

                sql_val = (
                    sql_brake_flag,                        # 1
                    *db_brake_left_value,                 # 12
                    *db_brake_right_value,                # 12
                    *db_brake_difference_value,           # 12
                    dt_brake_total_value,                 # 1
                    dt_brake_efficiency_value,            # 1
                    dt_id_user,                           # 1
                    dt_brake_post,                        # 1
                    dt_no_antri                           # 1
                )

                expected_params = 42 # brake_flag + 5 arrays ×12 + user/post/noantri
                if len(sql_val) != expected_params:
                    Logger.error(f"SQL Value count mismatch: expected {expected_params}, got {len(sql_val)}")
                else:
                    mycursor.execute(sql, sql_val)
                    mydb.commit()
                    Logger.info(f"Successfully updated load data for noantrian={dt_no_antri}")
            except Exception as e:
                toast_msg = f'Error Save Brake Data'
                toast(toast_msg)
                Logger.error(f"{self.name}: {toast_msg}, {e}")  

            try:
                mycursor = mydb.cursor()
                # Build SQL query safely
                sql1 = f"UPDATE {TB_DATA} SET handbrake_flag = %s"
                sql2 = (
                    ", handbrake_l_s1_value = %s, handbrake_l_s2_value = %s, handbrake_l_s3_value = %s, "
                    "handbrake_l_s4_value = %s, handbrake_l_s5_value = %s, handbrake_l_s6_value = %s, "
                    "handbrake_l_s7_value = %s, handbrake_l_s8_value = %s, handbrake_l_s9_value = %s, "
                    "handbrake_l_s10_value = %s, handbrake_l_s11_value = %s, handbrake_l_s12_value = %s"
                )
                sql3 = (
                    ", handbrake_r_s1_value = %s, handbrake_r_s2_value = %s, handbrake_r_s3_value = %s, "
                    "handbrake_r_s4_value = %s, handbrake_r_s5_value = %s, handbrake_r_s6_value = %s, "
                    "handbrake_r_s7_value = %s, handbrake_r_s8_value = %s, handbrake_r_s9_value = %s, "
                    "handbrake_r_s10_value = %s, handbrake_r_s11_value = %s, handbrake_r_s12_value = %s"
                )
                sql4 = (
                    ", handbrake_difference_s1_value = %s, handbrake_difference_s2_value = %s, handbrake_difference_s3_value = %s, "
                    "handbrake_difference_s4_value = %s, handbrake_difference_s5_value = %s, handbrake_difference_s6_value = %s, "
                    "handbrake_difference_s7_value = %s, handbrake_difference_s8_value = %s, handbrake_difference_s9_value = %s, "
                    "handbrake_difference_s10_value = %s, handbrake_difference_s11_value = %s, handbrake_difference_s12_value = %s"
                )
                sql6 = ", handbrake_total_value = %s, handbrake_efficiency_value = %s, handbrake_user = %s, handbrake_post = %s WHERE noantrian = %s"
                sql = sql1 + sql2 + sql3 + sql4 + sql5 + sql6

                sql_handbrake_flag = dt_handbrake_flag
                dt_handbrake_post = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())

                expected_len = 12
                arrays = {
                    'db_handbrake_left_value': db_handbrake_left_value,
                    'db_handbrake_right_value': db_handbrake_right_value,
                    'db_handbrake_difference_value': db_handbrake_difference_value,
                }

                for name, arr in arrays.items():
                    if not isinstance(arr, (list, tuple)) or len(arr) != expected_len:
                        Logger.error(f"{self.screen_manager.current}: {name} must be a list/tuple of 12 values. Got: {arr}")
                        raise ValueError(f"{name} must have exactly 12 elements")

                sql_val = (
                    sql_handbrake_flag,                         # 1
                    *db_handbrake_left_value,                   # 12
                    *db_handbrake_right_value,                  # 12
                    *db_handbrake_difference_value,             # 12
                    dt_handbrake_total_value,                   # 1
                    dt_handbrake_efficiency_value,              # 1
                    dt_id_user,                                 # 1
                    dt_handbrake_post,                          # 1
                    dt_no_antri                                 # 1
                )

                expected_params = 42  # handbrake_flag + 5 arrays ×12 + user/post/noantri
                if len(sql_val) != expected_params:
                    Logger.error(f"SQL Value count mismatch: expected {expected_params}, got {len(sql_val)}")
                else:
                    mycursor.execute(sql, sql_val)
                    mydb.commit()
                    Logger.info(f"Successfully updated load data for noantrian={dt_no_antri}")
            except Exception as e:
                toast_msg = f'Error Save Handbrake Data'
                toast(toast_msg)
                Logger.error(f"{self.name}: {toast_msg}, {e}")  

            self.exec_print()

            self.ids.bt_save.disabled = True
        
        except Exception as e:
            toast_msg = f'Error Save Data'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_print(self):
        try:
            global dt_load_flag, dt_brake_flag, dt_handbrake_flag
            # tb_status = mydb.cursor()
            # tb_status.execute(f"SELECT load_flag, brake_flag, handbrake_flag FROM {TB_DATA} WHERE noantrian = '{dt_no_antri}'")
            # result_tb_status = tb_status.fetchone()
            # mydb.commit()
            # db_status = np.array(result_tb_status).T
            # dt_load_flag            = int(db_status[0])
            # dt_brake_flag           = int(db_status[1])
            # dt_handbrake_flag       = int(db_status[2])
            
            self.exec_print_thermal()
            self.exec_print_pdf()

        except Exception as e:
            toast_msg = f'Gagal Mencetak Hasil Uji'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_print_pdf(self):
        global flag_play
        global count_starting, count_get_data
        global mydb, db_antrian
        global dt_no_antri, dt_no_pol, dt_no_uji, dt_nama, dt_jns_kend
        global dt_load_flag, dt_brake_flag, dt_handbrake_flag
        global db_load_left_value, db_load_right_value, db_load_total_value, db_load_flag
        global db_brake_left_value, db_brake_right_value, db_brake_total_value, db_brake_difference_value, db_brake_flag
        global db_handbrake_left_value, db_handbrake_right_value, db_handbrake_total_value, db_handbrake_difference_value, db_handbrake_flag
        global dt_load_total_value, dt_brake_total_value, dt_brake_efficiency_value, dt_brake_difference_value, dt_handbrake_total_value, dt_handbrake_efficiency_value, dt_handbrake_difference_value

        try:
            print_datetime = str(time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()))
            pdf = FPDF(format=(200, 600), unit='mm')
            pdf.add_page()
            pdf.set_xy(0, 2)
            pdf.image(f"assets/images/{IMG_LOGO_DISHUB}", w=30.0, h=0, x=20)
            pdf.set_xy(0, 2)
            pdf.image(f"assets/images/{IMG_LOGO_PEMKAB}", w=30.0, h=0, x=160)            
            pdf.set_font('Arial', 'B', 26.0)
            pdf.cell(ln=1, h=5.0, w=0)
            pdf.cell(ln=1, h=15.0, align='C', w=0, txt="DINAS PERHUBUNGAN", border=0)
            pdf.cell(ln=1, h=15.0, align='C', w=0, txt="UPTD PKB KAB. KUNINGAN", border=0)
            pdf.cell(ln=1, h=5.0, w=0)
            pdf.set_font('Arial', 'B', 21.0)
            pdf.cell(ln=1, h=10.0, align='L', w=0, txt=f"Tanggal: {print_datetime}", border=0)
            pdf.cell(ln=1, h=10.0, align='L', w=0, txt=f"No Reg Kend: {dt_no_pol}", border=0)
            pdf.cell(ln=0, h=10.0, align='L', w=0, txt=f"No Antrian: {dt_no_antri}", border=0)
            pdf.cell(ln=1, h=10.0, align='R', w=0, txt=f"No Uji: {dt_no_uji}", border=0)
            pdf.cell(ln=1, h=10.0, align='L', w=0, txt=f"Jenis Kendaraan: {dt_jns_kend}", border=0)
            pdf.cell(ln=0, h=10.0, align='L', w=0, txt=f"JBB: {dt_jbb}", border=0)
            pdf.cell(ln=1, h=10.0, align='R', w=0, txt=f"Berat Kosong: {float(dt_brt_ksg)}", border=0)
            pdf.cell(ln=1, h=10.0, w=0)
            pdf.set_font('Arial', '', 21.0)
            pdf.cell(ln=1, h=10.0, align='L', w=80, txt=f"AXLE LOAD")
            pdf.cell(ln=0, h=10.0, align='L', w=80, txt=f"Sumbu No.")
            pdf.cell(ln=0, h=10.0, align='L', w=40, txt=f"Kiri")
            pdf.cell(ln=0, h=10.0, align='L', w=40, txt=f"Kanan")
            pdf.cell(ln=1, h=10.0, align='L', w=40, txt=f"Total")
            for i in range(10):
                if (db_load_total_value[i] > 0):
                    pdf.cell(ln=0, h=10.0, align='L', w=80, txt=f"Sumbu {i+1}")
                    pdf.cell(ln=0, h=10.0, align='L', w=40, txt=f"{int(db_load_left_value[i])} kg")
                    pdf.cell(ln=0, h=10.0, align='L', w=40, txt=f"{int(db_load_right_value[i])} kg")
                    pdf.cell(ln=1, h=10.0, align='L', w=40, txt=f"{int(db_load_total_value[i])} kg")
            pdf.cell(ln=0, h=10.0, align='L', w=160, txt=f"Total :")
            pdf.cell(ln=1, h=10.0, align='L', w=40, txt=f"{int(dt_load_total_value)} kg")
            pdf.cell(ln=1, h=5.0, w=0)

            pdf.cell(ln=1, h=10.0, align='L', w=80, txt=f"REM UTAMA")
            pdf.cell(ln=0, h=10.0, align='L', w=80, txt=f"Sumbu No.")
            pdf.cell(ln=0, h=10.0, align='L', w=40, txt=f"Kiri")
            pdf.cell(ln=0, h=10.0, align='L', w=40, txt=f"Kanan")
            pdf.cell(ln=1, h=10.0, align='L', w=40, txt=f"Selisih")
            for i in range(10):
                if (db_brake_total_value[i] > 0):
                    pdf.cell(ln=0, h=10.0, align='L', w=80, txt=f"Sumbu {i+1}")
                    pdf.cell(ln=0, h=10.0, align='L', w=40, txt=f"{int(db_brake_left_value[i])} kg")
                    pdf.cell(ln=0, h=10.0, align='L', w=40, txt=f"{int(db_brake_right_value[i])} kg")
                    pdf.cell(ln=1, h=10.0, align='L', w=40, txt=f"{int(db_brake_difference_value[i])} %")
            pdf.cell(ln=0, h=10.0, align='L', w=160, txt=f"Total :")
            pdf.cell(ln=1, h=10.0, align='L', w=40, txt=f"{int(dt_brake_total_value)} kg")
            pdf.cell(ln=1, h=10.0, align='L', w=0, txt=f"Efisiensi : {str(np.round(dt_brake_efficiency_value, 1)).replace('.', ',')} %")
            pdf.cell(ln=0, h=10.0, align='L', w=80, txt=f"Status Pengujian :")
            str_brake_result = f'Lulus' if int(dt_brake_flag) == 2 else 'Tidak Lulus' if int(dt_brake_flag) == 1 else 'Belum Diuji'
            Logger.info(f"Status Brake: {str_brake_result}, Brake Flag: {dt_brake_flag}")
            pdf.cell(ln=1, h=10.0, align='R', w=30, txt=f"{str_brake_result}")
            pdf.cell(ln=1, h=5.0, w=0) 

            pdf.cell(ln=1, h=10.0, align='L', w=80, txt=f"REM PARKIR")
            pdf.cell(ln=0, h=10.0, align='L', w=80, txt=f"Sumbu No.")
            pdf.cell(ln=0, h=10.0, align='L', w=40, txt=f"Kiri")
            pdf.cell(ln=1, h=10.0, align='L', w=40, txt=f"Kanan")
            for i in range(10):
                if (db_handbrake_total_value[i] > 0):
                    pdf.cell(ln=0, h=10.0, align='L', w=80, txt=f"Sumbu {i+1}")
                    pdf.cell(ln=0, h=10.0, align='L', w=40, txt=f"{int(db_handbrake_left_value[i])} kg")
                    pdf.cell(ln=1, h=10.0, align='L', w=40, txt=f"{int(db_handbrake_right_value[i])} kg")
            pdf.cell(ln=0, h=10.0, align='L', w=160, txt=f"Total :")
            pdf.cell(ln=1, h=10.0, align='L', w=40, txt=f"{int(dt_handbrake_total_value)} kg")
            pdf.cell(ln=1, h=10.0, align='L', w=0, txt=f"Efisiensi : {str(np.round(dt_handbrake_efficiency_value, 1)).replace('.', ',')} %")
            pdf.cell(ln=0, h=10.0, align='L', w=80, txt=f"Status Pengujian :")
            str_handbrake_result = f'Lulus' if int(dt_handbrake_flag) == 2 else 'Tidak Lulus' if int(dt_handbrake_flag) == 1 else 'Belum Diuji'
            Logger.info(f"Status Handbrake: {str_handbrake_result}, Handbrake Flag: {dt_handbrake_flag}")
            pdf.cell(ln=1, h=10.0, align='R', w=30, txt=f"{str_handbrake_result}")
            pdf.cell(ln=1, h=5.0, w=0)

            pdf.cell(ln=1, h=10.0, align='C', w=0, txt=f"Resume Hasil Pengujian")
            pdf.set_font('Arial', 'B', 26.0)

            dt_brake_resume_flag = all(x == 2 for x in db_brake_flag if x != 0)
            if(dt_brake_resume_flag and int(dt_brake_flag) == 2 and int(dt_handbrake_flag) == 2):
                str_resume_result = f"LULUS"
            else:
                str_resume_result = f"TIDAK LULUS"
            pdf.cell(ln=1, h=10.0, align='C', w=0, txt=f"{str_resume_result}")

            documents_dir = os.path.join(os.environ["USERPROFILE"], "Documents")

            folder_name = f"Hasil_Uji_VIIS_AxleLoad_Brake_{time.strftime('%Y-%m-%d', time.localtime())}"
            date_folder_path = os.path.join(documents_dir, folder_name)
            
            if not os.path.exists(date_folder_path):
                os.makedirs(date_folder_path)
                toast(f"Folder created: {date_folder_path}")
            else:
                toast(f"Folder already exists: {date_folder_path}")

            pdf_filename = f"Hasil_Uji_No_{dt_no_antri}.pdf"
            pdf_path = os.path.join(date_folder_path, pdf_filename)

            pdf.output(pdf_path, 'F')
            toast(f"PDF saved to: {pdf_path}")
            os.startfile(pdf_path)

        except Exception as e:
            toast_msg = f'Gagal menyimpan ke pdf'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_print_thermal(self):
        global flag_play
        global count_starting, count_get_data
        global mydb, db_antrian
        global dt_no_antri, dt_no_pol, dt_no_uji, dt_nama, dt_jns_kend
        global dt_load_flag, dt_brake_flag, dt_handbrake_flag
        global db_load_left_value, db_load_right_value, db_load_total_value, db_load_flag
        global db_brake_left_value, db_brake_right_value, db_brake_total_value, db_brake_difference_value, db_brake_flag
        global db_handbrake_left_value, db_handbrake_right_value, db_handbrake_total_value, db_handbrake_difference_value, db_handbrake_flag
        global dt_load_total_value, dt_brake_total_value, dt_brake_efficiency_value, dt_brake_difference_value, dt_handbrake_total_value, dt_handbrake_efficiency_value, dt_handbrake_difference_value

        try:
            """ 9600 Baud, 8N1, Flow Control Enabled """
            printer = Serial(devfile=PRINTER_THERM_COM,
                    baudrate=PRINTER_THERM_BAUD,
                    bytesize=PRINTER_THERM_BYTESIZE,
                    parity=PRINTER_THERM_PARITY,
                    stopbits=PRINTER_THERM_STOPBITS,
                    timeout=PRINTER_THERM_TIMEOUT,
                    dsrdtr=PRINTER_THERM_DSRDTR,)
            print_datetime = str(time.strftime("%d %B %Y %H:%M:%S", time.localtime()))
            
            printer.image("assets/images/logo-dishub.png")
            printer.image("assets/images/logo-pandeglang.png")
            printer.textln(" \n ")
            printer.textln("VEHICLE INSPECTION INTEGRATION SYSTEM")
            printer.textln("AXLE LOAD & BRAKE")
            printer.textln("================================================================")
            printer.text(f"No Antrian: {dt_no_antri}\t")
            printer.text(f"No Reg: {dt_no_pol}\t")
            printer.textln(f"No Uji: {dt_no_uji}")
            printer.textln("  ")
            printer.textln(f"Jenis Kendaraan: {dt_jns_kend}")
            printer.textln("  ")
            printer.textln(f"Tanggal: {print_datetime}")
            printer.textln("  ")
            printer.textln(f"AXLE LOAD")
            printer.text(f"No. Sumbu \tKiri \tKanan \tTotal")
            for i in range(10):
                if (db_load_total_value[i] > 0.0):
                    printer.textln(f"S{i+1} \t{db_load_left_value[i]} \t{db_load_right_value[i]} \t{db_load_total_value[i]}")
            printer.textln(f"Nilai Axle Load Total : {dt_load_total_value}")
            printer.textln(f"Status Pengujian Axle Load : {'Lulus' if int(dt_load_flag) == 2 else 'Tidak Lulus' if int(dt_load_flag) == 1 else 'Belum Diuji'}")
            printer.textln("  ")
            printer.textln(f"REM UTAMA")
            printer.text(f"No. Sumbu \tKiri \tKanan \tTotal \tSelisih")
            for i in range(10):
                if (db_load_total_value[i] > 0.0):
                    printer.textln(f"S{i+1} \t{db_brake_left_value[i]} \t{db_brake_right_value[i]} \t{db_brake_total_value[i]} \t{db_brake_difference_value[i]}")
            printer.textln(f"Nilai Rem Utama Total : {dt_brake_total_value}")
            printer.textln(f"Nilai Efisiensi Rem Utama : {dt_brake_efficiency_value}")
            printer.textln(f"Status Pengujian Rem : {'Lulus' if int(dt_brake_flag) == 2 else 'Tidak Lulus' if int(dt_brake_flag) == 1 else 'Belum Diuji'}")
            printer.textln("  ")            
            printer.textln(f"REM PARKIR")
            printer.text(f"No. Sumbu \tKiri \tKanan \tTotal")
            for i in range(10):
                if (db_load_total_value[i] > 0.0):
                    printer.textln(f"S{i+1} \t{db_handbrake_left_value[i]} \t{db_handbrake_right_value[i]} \t{db_handbrake_total_value[i]}")
            printer.textln(f"Nilai Rem Parkir Total : {dt_handbrake_total_value}")
            printer.textln(f"Nilai Efisiensi Rem Parkir : {dt_handbrake_efficiency_value}")
            printer.textln(f"Status Pengujian Rem Parkir : {'Lulus' if int(dt_handbrake_flag) == 2 else 'Tidak Lulus' if int(dt_handbrake_flag) == 1 else 'Belum Diuji'}")
            printer.textln("  ")
            printer.textln("================================================================")
            printer.cut()

        except Exception as e:
            toast_msg = f'Gagal mencetak menggunakan Thermal Printer'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  


    def exec_navigate_main(self):
        try:
            self.screen_manager.current = 'screen_main'

        except Exception as e:
            toast_msg = f'Terjadi kesalahan saat berpindah ke halaman Utama'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

class RootScreen(ScreenManager):
    pass             

class LoadBrakeMeterApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.bind(on_resize=self.on_window_resize)

    def build(self):
        global window_size_x, window_size_y
        self.theme_cls.colors = colors
        self.theme_cls.primary_palette = "Gray"
        self.theme_cls.accent_palette = "Blue"
        self.theme_cls.theme_style = "Light"
        self.icon = 'assets/images/logo-load-app.png'
        window_size_y = Window.size[0]
        window_size_x = Window.size[1]
        self.set_dynamic_fonts(Window.size)

        LabelBase.register(
            name="Orbitron-Regular",
            fn_regular="assets/fonts/Orbitron-Regular.ttf")
        
        LabelBase.register(
            name="Draco",
            fn_regular="assets/fonts/Draco.otf")        

        LabelBase.register(
            name="Recharge",
            fn_regular="assets/fonts/Recharge.otf") 
        
        theme_font_styles.append('H1')
        self.theme_cls.font_styles["H1"] = [
            "Orbitron-Regular", 64, False, 0.15]       

        theme_font_styles.append('H2')
        self.theme_cls.font_styles["H2"] = [
            "Orbitron-Regular", 32, False, 0.15] 
        
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
            "Recharge", 11, False, 0.15] 

        theme_font_styles.append('Body1')
        self.theme_cls.font_styles["Body1"] = [
            "Recharge", 10, False, 0.15] 
        
        theme_font_styles.append('Button')
        self.theme_cls.font_styles["Button"] = [
            "Recharge", 9, False, 0.15] 

        theme_font_styles.append('Caption')
        self.theme_cls.font_styles["Caption"] = [
            "Recharge", 8, False, 0.15]       
        
        Window.fullscreen = 'auto'
        Builder.load_file('main.kv')
        return RootScreen()

    def on_window_resize(self, window, width, height):
        Logger.info(f"Window size: {width}x{height}")
        self.set_dynamic_fonts((width, height))
        self.refresh_all_fonts()

    def refresh_all_fonts(self):
        # Refresh fonts for all screens in the ScreenManager
        if hasattr(self, 'root') and hasattr(self.root, 'screens'):
            for screen in self.root.screens:
                self.refresh_fonts(screen)

    def refresh_fonts(self, widget):
        from kivymd.uix.label import MDLabel
        if isinstance(widget, MDLabel):
            original_style = widget.font_style
            temp_style = "Body1" if original_style != "Body1" else "H6"
            widget.font_style = temp_style
            widget.font_style = original_style
        if hasattr(widget, 'children'):
            for child in widget.children:
                self.refresh_fonts(child)

    def set_dynamic_fonts(self, size):
        try:
            screen_size_x = Window.system_size[0]
            screen_size_y = Window.system_size[1]
        except AttributeError:
            screen_size_x = Window._get_system_size()[0]
            screen_size_y = Window._get_system_size()[1]
        font_size_l = np.array([64, 32, 30, 20, 16, 11, 10, 9, 8])
        scale = min(screen_size_x / 1920, screen_size_y / 1080)
        font_size = np.round(font_size_l * scale, 0)
        Logger.info(f"Font resized: {font_size_l} to {font_size}")
        self.theme_cls.font_styles["H1"] = [
            "Orbitron-Regular", font_size[0], False, 0.15]
        self.theme_cls.font_styles["H2"] = [
            "Orbitron-Regular", font_size[1], False, 0.15]
        self.theme_cls.font_styles["H4"] = [
            "Recharge", font_size[2], False, 0.15]
        self.theme_cls.font_styles["H5"] = [
            "Recharge", font_size[3], False, 0.15]
        self.theme_cls.font_styles["H6"] = [
            "Recharge", font_size[4], False, 0.15]
        self.theme_cls.font_styles["Subtitle1"] = [
            "Recharge", font_size[5], False, 0.15]
        self.theme_cls.font_styles["Body1"] = [
            "Recharge", font_size[6], False, 0.15]
        self.theme_cls.font_styles["Button"] = [
            "Recharge", font_size[7], False, 0.15]
        self.theme_cls.font_styles["Caption"] = [
            "Recharge", font_size[8], False, 0.15]       

        if hasattr(self, 'root'):
            self.refresh_fonts(self.root)

if __name__ == '__main__':
    LoadBrakeMeterApp().run()