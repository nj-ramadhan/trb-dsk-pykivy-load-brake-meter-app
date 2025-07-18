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
DB_HOST = "127.0.0.1"
DB_USER = "kuningan2025"
DB_PASSWORD = "@kuningan2025"

# DB_HOST = "156.67.217.60"
# DB_USER = "pkbsorong2024!"
# DB_PASSWORD = "@Sorongpkb2024"

DB_NAME = "dishub"
TB_DATA = "tb_cekident"
TB_USER = "users"
TB_MERK = "merk"

FTP_HOST = "127.0.0.1"
FTP_USER = "kuningan2025"
FTP_PASS = "@kuningan2025"

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
STANDARD_MAX_BRAKE = float(config['standard']['STANDARD_MAX_BRAKE']) # %
STANDARD_MAX_DIFFERENCE_BRAKE = float(config['standard']['STANDARD_MAX_DIFFERENCE_BRAKE']) # %
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
            Logger.error(toast_msg, e)  

    def exec_navigate_home(self):
        try:
            self.screen_manager.current = 'screen_home'

        except Exception as e:
            toast_msg = f'Terjadi kesalahan saat berpindah ke halaman Beranda'
            toast(toast_msg)
            Logger.error(toast_msg, e)

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
        global flag_conn_stat, flag_play
        global count_starting, count_get_data
        global db_load_left_value, db_load_right_value, db_load_total_value
        global dt_load_total_value, dt_load_flag, dt_load_user, dt_load_post
        global db_brake_left_value, db_brake_right_value, db_brake_total_value, db_brake_efficiency_value, db_brake_difference_value
        global dt_brake_total_value, dt_brake_efficiency_value, dt_brake_difference_value, dt_brake_flag, dt_brake_user, dt_brake_post
        global db_handbrake_left_value, db_handbrake_right_value, db_handbrake_total_value, db_handbrake_efficiency_value, db_handbrake_difference_value
        global dt_handbrake_total_value, dt_handbrake_efficiency_value, dt_handbrake_difference_value, dt_handbrake_flag, dt_handbrake_user, dt_handbrake_post
        global dt_user, dt_no_antrian, dt_no_pol, dt_no_uji, dt_nama, dt_jenis_kendaraan
        global dt_test_number, dt_dash_pendaftaran, dt_dash_belum_uji, dt_dash_sudah_uji
        global flag_cylinder

        flag_conn_stat = flag_play = False

        count_starting = COUNT_STARTING
        count_get_data = COUNT_ACQUISITION

        db_load_left_value = np.zeros(10, dtype=float)
        db_load_right_value = np.zeros(10, dtype=float)
        db_load_total_value = np.zeros(10, dtype=float)
        dt_load_total_value = dt_load_flag = 0

        db_brake_left_value = np.zeros(10, dtype=float)
        db_brake_right_value = np.zeros(10, dtype=float)
        db_brake_total_value = np.zeros(10, dtype=float)
        db_brake_efficiency_value = np.zeros(10, dtype=float)
        db_brake_difference_value = np.zeros(10, dtype=float)
        dt_brake_total_value = dt_brake_efficiency_value = dt_brake_difference_value = dt_brake_flag = 0

        db_handbrake_left_value = np.zeros(10, dtype=float)
        db_handbrake_right_value = np.zeros(10, dtype=float)
        db_handbrake_total_value = np.zeros(10, dtype=float)
        db_handbrake_efficiency_value = np.zeros(10, dtype=float)
        db_handbrake_difference_value = np.zeros(10, dtype=float)
        dt_handbrake_total_value = dt_handbrake_efficiency_value = dt_handbrake_difference_value = dt_handbrake_flag = 0

        dt_load_user = dt_brake_user = dt_handbrake_user = 1
        dt_load_post = dt_brake_post = dt_handbrake_post = str(time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()))

        dt_user = dt_no_antrian = dt_no_pol = dt_no_uji = dt_nama = dt_jenis_kendaraan = ""

        dt_test_number = dt_dash_pendaftaran = dt_dash_belum_uji = dt_dash_sudah_uji = 0

        flag_cylinder = False

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
            screen_calibration = self.screen_manager.get_screen('screen_calibration')

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
                screen_resume.ids.bt_print.disabled = False
                screen_load_meter.ids.bt_reload.md_bg_color = colors['Red']['A200']
                screen_load_meter.ids.bt_reload.disabled = False
                screen_brake_meter.ids.bt_reload.md_bg_color = colors['Red']['A200']
                screen_brake_meter.ids.bt_reload.disabled = False
                screen_handbrake_meter.ids.bt_reload.md_bg_color = colors['Red']['A200']
                screen_handbrake_meter.ids.bt_reload.disabled = False   
            else:
                screen_resume.ids.bt_save.disabled = True
                screen_resume.ids.bt_print.disabled = True
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
            
            for i in range(10):
                if(dt_test_number == i):
                    screen_menu.ids[f'bt_S{i}'].md_bg_color = colors['Red']['A200']
                else:
                    screen_menu.ids[f'bt_S{i}'].md_bg_color = colors['Green']['200']

            if(not flag_conn_stat):
                self.ids.lb_comm.color = colors['Red']['A200']
                self.ids.lb_comm.text = 'PLC Tidak Terhubung'
                screen_home.ids.lb_comm.color = colors['Red']['A200']
                screen_home.ids.lb_comm.text = 'PLC Tidak Terhubung'
                screen_login.ids.lb_comm.color = colors['Red']['A200']
                screen_login.ids.lb_comm.text = 'PLC Tidak Terhubung'
                screen_menu.ids.lb_comm.color = colors['Red']['A200']
                screen_menu.ids.lb_comm.text = 'PLC Tidak Terhubung'
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

            self.ids.bt_logout.disabled = False if dt_user != '' else True
            self.ids.bt_add_queue.disabled = False if dt_user != '' else True

            self.ids.lb_operator.text = f'Login Sebagai: {dt_user}' if dt_user != '' else 'Silahkan Login'
            screen_home.ids.lb_operator.text = f'Login Sebagai: {dt_user}' if dt_user != '' else 'Silahkan Login'
            screen_login.ids.lb_operator.text = f'Login Sebagai: {dt_user}' if dt_user != '' else 'Silahkan Login'

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
            toast_msg = f'Gagal Memperbaharui Koneksi: {e}'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  
            flag_conn_stat = False

    def unsigned_to_signed(self, val):
        if val >= 32768:
            return val - 65536
        return val

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

            # Simulated data 
            # db_load_left_value[dt_test_number] = np.round(np.random.randint(0, 10000) / 10, 2)  
            # db_load_right_value[dt_test_number] = np.round(np.random.randint(0, 10000) / 10, 2)
            # db_brake_left_value[dt_test_number] = np.round(np.random.randint(0, 10000) / 10, 2)
            # db_brake_right_value[dt_test_number] = np.round(np.random.randint(0, 10000) / 10, 2)
            # db_handbrake_left_value[dt_test_number] = np.round(np.random.randint(0, 10000) / 10, 2)
            # db_handbrake_right_value[dt_test_number] = np.round(np.random.randint(0, 10000) / 10, 2)
            
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                load_l_registers = MODBUS_CLIENT.read_holding_registers(REGISTER_DATA_LOAD_L, count=1, slave=1) #V1400
                load_r_registers = MODBUS_CLIENT.read_holding_registers(REGISTER_DATA_LOAD_R, count=1, slave=1) #V1410
                brake_l_registers = MODBUS_CLIENT.read_holding_registers(REGISTER_DATA_BRAKE_L, count=1, slave=1) #V1420
                brake_r_registers = MODBUS_CLIENT.read_holding_registers(REGISTER_DATA_BRAKE_R, count=1, slave=1) #V1430
                MODBUS_CLIENT.close()

                db_load_left_value[dt_test_number] = int(self.unsigned_to_signed(load_l_registers.registers[0]))
                db_load_right_value[dt_test_number] = int(self.unsigned_to_signed(load_r_registers.registers[0]))
                db_brake_left_value[dt_test_number] = int(self.unsigned_to_signed(brake_l_registers.registers[0]))
                db_brake_right_value[dt_test_number] = int(self.unsigned_to_signed(brake_r_registers.registers[0]))
                db_handbrake_left_value[dt_test_number] = int(self.unsigned_to_signed(brake_l_registers.registers[0]))
                db_handbrake_right_value[dt_test_number] = int(self.unsigned_to_signed(brake_r_registers.registers[0]))

                db_load_left_value[dt_test_number] = db_load_left_value[dt_test_number] if db_load_left_value[dt_test_number] >= 0 and db_load_left_value[dt_test_number] <= MAX_LOAD_DATA else 0
                db_load_right_value[dt_test_number] = db_load_right_value[dt_test_number] if db_load_right_value[dt_test_number] >= 0 and db_load_right_value[dt_test_number] <= MAX_LOAD_DATA else 0
                db_brake_left_value[dt_test_number] = db_brake_left_value[dt_test_number] if db_brake_left_value[dt_test_number] >= 0 and db_brake_left_value[dt_test_number] <= MAX_BRAKE_DATA else 0
                db_brake_right_value[dt_test_number] = db_brake_right_value[dt_test_number] if db_brake_right_value[dt_test_number] >= 0 and db_brake_right_value[dt_test_number] <= MAX_BRAKE_DATA else 0
                db_handbrake_left_value[dt_test_number] = db_handbrake_left_value[dt_test_number] if db_handbrake_left_value[dt_test_number] >= 0 and db_handbrake_left_value[dt_test_number] <= MAX_BRAKE_DATA else 0
                db_handbrake_right_value[dt_test_number] = db_handbrake_right_value[dt_test_number] if db_handbrake_right_value[dt_test_number] >= 0 and db_handbrake_right_value[dt_test_number] <= MAX_BRAKE_DATA else 0

            if self.screen_manager.current == 'screen_load_meter':
                # if(dt_test_number == 0 and db_load_right_value[dt_test_number] >= 60):
                #     db_load_right_value[dt_test_number] = db_load_right_value[dt_test_number] - 60.0
                db_load_total_value[dt_test_number] = int(db_load_left_value[dt_test_number] + db_load_right_value[dt_test_number])
                dt_load_total_value = int(np.sum(db_load_total_value))
                Logger.info(f"{self.screen_manager.current}: DB Load Left = {db_load_left_value}, DB Load Right = {db_load_right_value}, DB Load Total = {db_load_total_value}")
                Logger.info(f"{self.screen_manager.current}: DB Load Left = {db_load_left_value[dt_test_number]}, DB Load Right = {db_load_right_value[dt_test_number]}, DB Load Total = {db_load_total_value[dt_test_number]}")

            if self.screen_manager.current == 'screen_brake_meter':
                db_brake_total_value[dt_test_number] = int(db_brake_left_value[dt_test_number] + db_brake_right_value[dt_test_number])
                db_brake_efficiency_value[dt_test_number] = np.round((db_brake_total_value[dt_test_number] / dt_load_total_value) * 100, 1)
                db_brake_difference_value[dt_test_number] = np.round((np.abs(db_brake_left_value[dt_test_number] - db_brake_right_value[dt_test_number]) / db_load_total_value[dt_test_number]) * 100, 1)
                dt_brake_total_value = int(np.sum(db_brake_total_value))
                dt_brake_efficiency_value = np.round((dt_brake_total_value / dt_load_total_value) * 100, 1)
                dt_brake_difference_value = int(np.sum(db_brake_difference_value))
                Logger.info(f"{self.screen_manager.current}: DB Brake Left = {db_brake_left_value}, DB Brake Right = {db_brake_right_value}, DB Brake Total = {db_brake_total_value}, DB Brake Efficiency = {db_brake_efficiency_value}, DB Brake Difference = {db_brake_difference_value}")
                Logger.info(f"{self.screen_manager.current}: DB Brake Left = {db_brake_left_value[dt_test_number]}, DB Brake Right = {db_brake_right_value[dt_test_number]}, DB Brake Total = {db_brake_total_value[dt_test_number]}, DB Brake Efficiency = {db_brake_efficiency_value[dt_test_number]}, DB Brake Difference = {db_brake_difference_value[dt_test_number]}")

            if self.screen_manager.current == 'screen_handbrake_meter':
                db_handbrake_total_value[dt_test_number] = int(db_handbrake_left_value[dt_test_number] + db_handbrake_right_value[dt_test_number])
                db_handbrake_efficiency_value[dt_test_number] = np.round((db_brake_total_value[dt_test_number] / int(dt_jbb)) * 100, 1)
                db_handbrake_difference_value[dt_test_number] = np.round((np.abs(db_handbrake_left_value[dt_test_number] - db_handbrake_right_value[dt_test_number]) / db_load_total_value[dt_test_number]) * 100, 1)
                dt_handbrake_total_value = int(np.sum(db_handbrake_total_value))
                dt_handbrake_efficiency_value = np.round((dt_handbrake_total_value / dt_load_total_value) * 100, 1)
                dt_handbrake_difference_value = int(np.sum(db_handbrake_difference_value))
                Logger.info(f"{self.screen_manager.current}: DB Handbrake Left = {db_handbrake_left_value}, DB Handbrake Right = {db_handbrake_right_value}, DB Handbrake Total = {db_handbrake_total_value}, DB Handbrake Efficiency = {db_handbrake_efficiency_value}, DB Handbrake Difference = {db_handbrake_difference_value}")
                Logger.info(f"{self.screen_manager.current}: DB Handbrake Left = {db_handbrake_left_value[dt_test_number]}, DB Handbrake Right = {db_handbrake_right_value[dt_test_number]}, DB Handbrake Total = {db_handbrake_total_value[dt_test_number]}, DB Handbrake Efficiency = {db_handbrake_efficiency_value[dt_test_number]}, DB Handbrake Difference = {db_handbrake_difference_value[dt_test_number]}")

        except Exception as e:
            toast_msg = f'Gagal Mengambil Data: {e}'
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_reload_database(self):
        global mydb
        try:
            mydb = mysql.connector.connect(host = DB_HOST,user = DB_USER,password = DB_PASSWORD,database = DB_NAME)
        except Exception as e:
            toast_msg = f'Gagal Menginisiasi Database: {e}'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_reload_table(self):
        global mydb, db_antrian, db_merk
        global dt_dash_pendaftaran, dt_dash_belum_uji, dt_dash_sudah_uji

        try:
            tb_antrian = mydb.cursor()
            tb_antrian.execute(f"SELECT noantrian, nopol, nouji, load_flag, brake_flag, handbrake_flag, user, merk, type, idjeniskendaraan, jbb, berat_kosong, warna FROM {TB_DATA}")
            result_tb_antrian = tb_antrian.fetchall()
            mydb.commit()
            db_antrian = np.array(result_tb_antrian).T
            db_pendaftaran = np.array(result_tb_antrian)
            dt_dash_pendaftaran = db_pendaftaran[:,3].size
            dt_dash_belum_uji = np.where(db_pendaftaran[:,3] == 0)[0].size
            dt_dash_sudah_uji = np.where(db_pendaftaran[:,3] == 1)[0].size

            # tb_merk = mydb.cursor()
            # tb_merk.execute(f"SELECT ID, DESCRIPTION FROM {TB_MERK}")
            # result_tb_merk = tb_merk.fetchall()
            # mydb.commit()
            # db_merk = np.array(result_tb_merk)
        except Exception as e:
            toast_msg = f'Error Fetch Database: {e}'
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

        try:            
            layout_list = self.ids.layout_list
            layout_list.clear_widgets(children=None)
        except Exception as e:
            toast_msg = f'Error Remove Widget: {e}'
            Logger.error(f"{self.name}: {toast_msg}, {e}")  
        
        try:           
            layout_list = self.ids.layout_list
            for i in range(db_antrian[0,:].size):
                layout_list.add_widget(
                    MDCard(
                        MDLabel(text=f"{db_antrian[0, i]}", size_hint_x= 0.05),
                        MDLabel(text=f"{db_antrian[1, i]}", size_hint_x= 0.08),
                        MDLabel(text=f"{db_antrian[2, i]}", size_hint_x= 0.08),
                        MDLabel(text='Lulus' if (int(db_antrian[3, i]) == 2) else 'Tidak Lulus' if (int(db_antrian[3, i]) == 1) else 'Belum Tes', size_hint_x= 0.07),
                        MDLabel(text='Lulus' if (int(db_antrian[4, i]) == 2) else 'Tidak Lulus' if (int(db_antrian[4, i]) == 1) else 'Belum Tes', size_hint_x= 0.07),
                        MDLabel(text='Lulus' if (int(db_antrian[5, i]) == 2) else 'Tidak Lulus' if (int(db_antrian[5, i]) == 1) else 'Belum Tes', size_hint_x= 0.07),
                        MDLabel(text=f"{db_antrian[6, i]}", size_hint_x= 0.08),
                        # MDLabel(text=f"{db_merk[np.where(db_merk == db_antrian[7, i])[0][0],1]}", size_hint_x= 0.08),
                        MDLabel(text=f"{db_antrian[7, i]}", size_hint_x= 0.08),
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
            Logger.error(f"{self.name}: {toast_msg}, {e}")

    def on_antrian_row_press(self, instance):
        global dt_no_antrian, dt_no_pol, dt_no_uji, dt_nama, dt_load_flag, dt_brake_flag, dt_handbrake_flag
        global dt_merk, dt_type, dt_jenis_kendaraan, dt_jbb, dt_berat_kosong, dt_warna
        global db_antrian, db_merk

        try:
            row = int(str(instance.id).replace("card_antrian",""))
            dt_no_antrian           = f"{db_antrian[0, row]}"
            dt_no_pol               = f"{db_antrian[1, row]}"
            dt_no_uji               = f"{db_antrian[2, row]}"
            dt_load_flag            = 'Lulus' if (int(db_antrian[3, row]) == 2) else 'Tidak Lulus' if (int(db_antrian[3, row]) == 1) else 'Belum Tes'
            dt_brake_flag           = 'Lulus' if (int(db_antrian[4, row]) == 2) else 'Tidak Lulus' if (int(db_antrian[4, row]) == 1) else 'Belum Tes'
            dt_handbrake_flag       = 'Lulus' if (int(db_antrian[5, row]) == 2) else 'Tidak Lulus' if (int(db_antrian[5, row]) == 1) else 'Belum Tes'
            dt_nama                 = f"{db_antrian[6, row]}"
            # dt_merk                 = f"{db_merk[np.where(db_merk == db_antrian[7, row])[0][0],1]}"
            dt_merk                 = f"{db_antrian[7, row]}"
            dt_type                 = f"{db_antrian[8, row]}"
            dt_jenis_kendaraan      = f"{db_antrian[9, row]}"
            dt_jbb                  = f"{db_antrian[10, row]}"
            dt_berat_kosong         = f"{db_antrian[11, row]}"
            dt_warna                = f"{db_antrian[12, row]}"
                        
            self.exec_start()

        except Exception as e:
            toast_msg = f'Error Execute Command from Table Row: {e}'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  
            
    def exec_start(self):
        global dt_load_flag, dt_brake_flag, dt_handbrake_flag, dt_no_antrian, dt_user
        global flag_play
        if (dt_user != ''):
            if (dt_load_flag == 'Belum Tes' or dt_brake_flag == 'Belum Tes' or dt_handbrake_flag == 'Belum Tes'):
                self.open_screen_menu()
            else:
                toast_msg = f'No. Antrian {dt_no_antrian} Sudah Tes'
                toast(toast_msg)
                Logger.info(f"{self.name}: {toast_msg}")
        else:
            toast_msg = f'Silahkan Login Untuk Melakukan Pengujian'
            toast(toast_msg)
            Logger.info(f"{self.name}: {toast_msg}")      

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


    def exec_navigate_calibration(self):
        global dt_user
        try:
            self.screen_manager.current = 'screen_calibration'

        except Exception as e:
            toast_msg = f'Error Navigate to Calibration Screen: {e}'
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

    def exec_navigate_main(self):
        try:
            self.screen_manager.current = 'screen_main'

        except Exception as e:
            toast_msg = f'Error Navigate to Main Screen: {e}'
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
        try:
            self.screen_manager.current = 'screen_main'

        except Exception as e:
            toast_msg = f'Terjadi kesalahan saat berpindah ke halaman Utama'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_register(self):
        try:
            # Get the last noantrian
            mycursor = mydb.cursor()
            mycursor.execute(f"SELECT MAX(noantrian) FROM {TB_DATA}")
            result = mycursor.fetchone()
            last_noantrian = int(result[0]) if result[0] is not None else 0
            noantrian = f"{last_noantrian + 1:04d}"

            nopol = self.ids.tx_nopol.text
            nouji = self.ids.tx_nouji.text
            merk = self.ids.tx_merk.text
            tipe = self.ids.tx_type.text
            idjeniskendaraan = self.ids.tx_idjeniskendaraan.text
            jbb = self.ids.tx_jbb.text
            berat_kosong = self.ids.tx_berat_kosong.text
            warna = self.ids.tx_warna.text

            mycursor = mydb.cursor()
            sql = f"INSERT INTO {TB_DATA} (noantrian, nopol, nouji, NEW_NOUJI, merk, type, idjeniskendaraan, jbb, berat_kosong, warna) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            values = (noantrian, nopol, nouji, nouji, merk, tipe, idjeniskendaraan, jbb, berat_kosong, warna)
            mycursor.execute(sql, values)
            mydb.commit()

            toast("Data berhasil didaftarkan")
            self.screen_manager.current = 'screen_main'

        except Exception as e:
            toast_msg = f'Terjadi kesalahan saat mendaftar: {e}'
            toast(f"Terjadi kesalahan saat mendaftar: {e}")

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
        except Exception as e:
            toast_msg = f"error send exec_cylinder_up data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

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
        except Exception as e:
            toast_msg = f"error send exec_cylinder_down data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_cylinder_stop(self):
        global flag_conn_stat

        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_coil(3082, False, slave=1) #M10
                MODBUS_CLIENT.write_coil(3083, False, slave=1) #M11
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send exec_cylinder_stop data to PLC Slave"
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
        except Exception as e:
            toast_msg = f"error send exec_cylinder_up data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

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
        except Exception as e:
            toast_msg = f"error send exec_cylinder_down data to PLC Slave"
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")

    def exec_cylinder_stop(self):
        global flag_conn_stat

        try:
            if flag_conn_stat:
                MODBUS_CLIENT.connect()
                MODBUS_CLIENT.write_coil(3082, False, slave=1) #M10
                MODBUS_CLIENT.write_coil(3083, False, slave=1) #M11
                MODBUS_CLIENT.close()
        except Exception as e:
            toast_msg = f"error send exec_cylinder_stop data to PLC Slave"
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
        global dt_load_flag, dt_brake_flag, dt_handbrake_flag
        self.exec_reload_table_detail()
        try:
            self.ids.lb_load_left_sum.text = f'{int(np.sum(db_load_left_value))} kg'
            self.ids.lb_load_right_sum.text = f'{int(np.sum(db_load_right_value))} kg'
            self.ids.lb_load_total_sum.text = f'{int(dt_load_total_value)} kg'
            self.ids.lb_brake_left_sum.text = f'{int(np.sum(db_brake_left_value))} kg'
            self.ids.lb_brake_right_sum.text = f'{int(np.sum(db_brake_right_value))} kg'
            self.ids.lb_brake_total_sum.text = f'{int(dt_brake_total_value)} kg'
            self.ids.lb_brake_diff_sum.text = f'{np.round(dt_brake_difference_value, 1)} %'
            self.ids.lb_brake_efficiency.text = f'{np.round(dt_brake_efficiency_value, 1)} %'
            self.ids.lb_handbrake_left_sum.text = f'{int(np.sum(db_handbrake_left_value))} kg'
            self.ids.lb_handbrake_right_sum.text = f'{int(np.sum(db_handbrake_right_value))} kg'
            self.ids.lb_handbrake_total_sum.text = f'{int(dt_handbrake_total_value)} kg'
            self.ids.lb_handbrake_efficiency.text = f'{np.round(dt_handbrake_efficiency_value, 1)} %'

            if(np.abs(int(np.sum(db_load_left_value)) - int(np.sum(db_load_right_value))) <= (0.1 * int(dt_load_total_value))):
                dt_load_flag = "Lulus"  
            else:
                dt_load_flag = "Tidak Lulus"

            if(dt_brake_efficiency_value >= 50 and dt_brake_difference_value <= 8):
                dt_brake_flag = "Lulus"             
            else:
                dt_brake_flag = "Tidak Lulus"
            
            if(dt_handbrake_efficiency_value >= 12):
                dt_handbrake_flag = "Lulus"
            else:
                dt_handbrake_flag = "Tidak Lulus"

            if(dt_load_flag == "Lulus" and dt_brake_flag == "Lulus" and dt_handbrake_flag == "Lulus"):
                self.ids.lb_test_result.md_bg_color = colors['Green']['200']
                self.ids.lb_test_result.text_color = colors['Green']['700']
                self.ids.lb_test_result.text = f"LULUS"
            else:
                self.ids.lb_test_result.md_bg_color = colors['Red']['A200']
                self.ids.lb_test_result.text_color = colors['Red']['A700']
                self.ids.lb_test_result.text = f"TIDAK LULUS"
                                
        except Exception as e:
            toast_msg = f'Error Create Resume: {e}'
            Logger.error(f"{self.name}: {toast_msg}, {e}")   


    def exec_reload_table_detail(self):
        global dt_user, dt_no_antrian, dt_no_pol, dt_no_uji, dt_nama, dt_jenis_kendaraan
        global dt_load_flag, db_load_left_value, db_load_right_value, db_load_total_value, dt_load_user, dt_load_post
        global dt_brake_flag, db_brake_left_value, db_brake_right_value, db_brake_total_value, db_brake_efficiency_value, db_brake_difference_value, dt_brake_user, dt_brake_post
        global dt_handbrake_flag, db_handbrake_left_value, db_handbrake_right_value, db_handbrake_total_value, db_handbrake_efficiency_value, db_handbrake_difference_value, dt_handbrake_user, dt_handbrake_post
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
                            MDLabel(text=f"Sumbu {i+1}", size_hint_x= 0.25),
                            MDLabel(text=f"{db_load_left_value[i]}", size_hint_x= 0.25),
                            MDLabel(text=f"{db_load_right_value[i]}", size_hint_x= 0.25),
                            MDLabel(text=f"{db_load_total_value[i]}", size_hint_x= 0.25),
                            padding = 20,
                            size_hint_y=None,
                            height="40dp",                          
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
                            MDLabel(text=f"Sumbu {i+1}", size_hint_x= 0.25),
                            MDLabel(text=f"{db_brake_left_value[i]}", size_hint_x= 0.1875),
                            MDLabel(text=f"{db_brake_right_value[i]}", size_hint_x= 0.1875),
                            MDLabel(text=f"{db_brake_total_value[i]}", size_hint_x= 0.1875),
                            MDLabel(text=f"{db_brake_difference_value[i]}", size_hint_x= 0.1875),
                            padding = 20,
                            size_hint_y=None,
                            height="40dp",
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
                            MDLabel(text=f"Sumbu {i+1}", size_hint_x= 0.25),
                            MDLabel(text=f"{db_handbrake_left_value[i]}", size_hint_x= 0.25),
                            MDLabel(text=f"{db_handbrake_right_value[i]}", size_hint_x= 0.25),
                            MDLabel(text=f"{db_handbrake_total_value[i]}", size_hint_x= 0.25),
                            padding = 20,
                            size_hint_y=None,
                            height="40dp",
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
        global db_load_left_value, db_load_right_value, db_load_total_value
        global db_brake_left_value, db_brake_right_value, db_brake_total_value, db_brake_efficiency_value, db_brake_difference_value
        global db_handbrake_left_value, db_handbrake_right_value, db_handbrake_total_value, db_handbrake_efficiency_value, db_handbrake_difference_value
        global dt_load_total_value, dt_brake_total_value, dt_brake_efficiency_value, dt_brake_difference_value, dt_handbrake_total_value, dt_handbrake_efficiency_value, dt_handbrake_difference_value
        global dt_test_number

        try:
            mycursor = mydb.cursor()
            sql = f"UPDATE {TB_DATA} SET load_flag = %s, load_l_value = %s, load_r_value = %s, load_total_value = %s, load_user = %s, load_post = %s WHERE noantrian = %s"
            sql_load_flag = (2 if dt_load_flag == "Lulus" else 1)
            dt_load_post = str(time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()))
            sql_val = (sql_load_flag, float(np.average(db_load_left_value)), float(np.average(db_load_right_value)), dt_load_total_value, dt_load_user, dt_load_post, dt_no_antrian)
            mycursor.execute(sql, sql_val)
            mydb.commit()

            mycursor = mydb.cursor()
            sql = f"UPDATE {TB_DATA} SET brake_flag = %s, brake_l_value = %s, brake_r_value = %s, brake_total_value = %s, brake_efficiency_value = %s, brake_difference_value = %s, load_user = %s, load_post = %s WHERE noantrian = %s"
            sql_brake_flag = (2 if dt_brake_flag == "Lulus" else 1)
            dt_brake_post = str(time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()))
            sql_val = (sql_brake_flag, float(np.average(db_brake_left_value)), float(np.average(db_brake_right_value)), dt_brake_total_value, dt_brake_efficiency_value, dt_brake_difference_value, dt_load_user, dt_brake_post, dt_no_antrian)
            mycursor.execute(sql, sql_val)
            mydb.commit()

            mycursor = mydb.cursor()
            sql = f"UPDATE {TB_DATA} SET handbrake_flag = %s, handbrake_l_value = %s, handbrake_r_value = %s, handbrake_total_value = %s, handbrake_efficiency_value = %s, handbrake_difference_value = %s, load_user = %s, load_post = %s WHERE noantrian = %s"
            sql_handbrake_flag = (2 if dt_handbrake_flag == "Lulus" else 1)
            dt_handbrake_post = str(time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()))
            sql_val = (sql_handbrake_flag, float(np.average(db_handbrake_left_value)), float(np.average(db_handbrake_right_value)), dt_handbrake_total_value, dt_handbrake_efficiency_value, dt_handbrake_difference_value, dt_load_user, dt_handbrake_post, dt_no_antrian)
            mycursor.execute(sql, sql_val)
            mydb.commit()

            self.ids.bt_save.disabled = True
        
        except Exception as e:
            toast_msg = f'Error Save Data'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_print(self):
        try:
            global dt_load_flag, dt_brake_flag, dt_handbrake_flag
            tb_status = mydb.cursor()
            tb_status.execute(f"SELECT load_flag, brake_flag, handbrake_flag FROM {TB_DATA} WHERE noantrian = '{dt_no_antrian}'")
            result_tb_status = tb_status.fetchone()
            mydb.commit()
            db_status = np.array(result_tb_status).T
            dt_load_flag            = int(db_status[0])
            dt_brake_flag           = int(db_status[1])
            dt_handbrake_flag       = int(db_status[2])
            
            self.exec_print_thermal()
            self.exec_print_pdf()

            self.ids.bt_print.disabled = True

        except Exception as e:
            toast_msg = f'Gagal Mencetak Hasil Uji'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_print_pdf(self):
        global flag_play
        global count_starting, count_get_data
        global mydb, db_antrian
        global dt_no_antrian, dt_no_pol, dt_no_uji, dt_nama, dt_jenis_kendaraan
        global dt_load_flag, dt_brake_flag, dt_handbrake_flag
        global db_load_left_value, db_load_right_value, db_load_total_value
        global db_brake_left_value, db_brake_right_value, db_brake_total_value, db_brake_efficiency_value, db_brake_difference_value
        global db_handbrake_left_value, db_handbrake_right_value, db_handbrake_total_value, db_handbrake_efficiency_value, db_handbrake_difference_value
        global dt_load_total_value, dt_brake_total_value, dt_brake_efficiency_value, dt_brake_difference_value, dt_handbrake_total_value, dt_handbrake_efficiency_value, dt_handbrake_difference_value

        try:
            print_datetime = str(time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()))
            pdf = FPDF()
            pdf.add_page()
            pdf.set_xy(0, 2)
            pdf.image("assets/images/logo-dishub.png", w=30.0, h=0, x=90)
            pdf.set_font('Arial', 'B', 24.0)
            pdf.cell(ln=1, h=5.0, w=0)
            pdf.cell(ln=1, h=15.0, align='C', w=0, txt="DINAS PERHUBUNGAN", border=0)
            pdf.cell(ln=1, h=15.0, align='C', w=0, txt="UPTD PKB KAB. KUNINGAN", border=0)
            pdf.cell(ln=1, h=5.0, w=0)
            pdf.set_font('Arial', 'B', 14.0)
            pdf.cell(ln=0, h=10.0, align='L', w=0, txt=f"Tanggal: {print_datetime}", border=0)
            pdf.cell(ln=1, h=10.0, align='R', w=0, txt=f"No Reg Kend: {dt_no_pol}", border=0)
            pdf.cell(ln=0, h=10.0, align='L', w=0, txt=f"No Antrian: {dt_no_antrian}", border=0)
            pdf.cell(ln=1, h=10.0, align='R', w=0, txt=f"No Uji: {dt_no_uji}", border=0)
            pdf.cell(ln=1, h=10.0, align='L', w=0, txt=f"Jenis Kendaraan: {dt_jenis_kendaraan}", border=0)
            pdf.cell(ln=1, h=10.0, align='L', w=0, txt=f"Nama: {dt_nama}", border=0)
            pdf.cell(ln=0, h=10.0, align='L', w=0, txt=f"JBB: {dt_jbb}", border=0)
            pdf.cell(ln=1, h=10.0, align='R', w=0, txt=f"Berat Kosong: {float(dt_berat_kosong)}", border=0)
            pdf.cell(ln=1, h=10.0, w=0)
            pdf.set_font('Arial', '', 14.0)
            pdf.cell(ln=1, h=10.0, align='L', w=80, txt=f"AXLE LOAD")
            pdf.cell(ln=0, h=10.0, align='L', w=80, txt=f"No. Sumbu")
            pdf.cell(ln=0, h=10.0, align='L', w=80, txt=f"Kiri")
            pdf.cell(ln=0, h=10.0, align='L', w=80, txt=f"Kanan")
            pdf.cell(ln=1, h=10.0, align='L', w=80, txt=f"Total")
            for i in range(10):
                if (db_load_total_value[i] > 0):
                    pdf.cell(ln=0, h=10.0, align='L', w=80, txt=f"S{i+1}")
                    pdf.cell(ln=0, h=10.0, align='L', w=80, txt=f"{int(db_load_left_value[i])} kg")
                    pdf.cell(ln=0, h=10.0, align='L', w=80, txt=f"{int(db_load_right_value[i])} kg")
                    pdf.cell(ln=1, h=10.0, align='L', w=80, txt=f"{int(db_load_total_value[i])} kg")
            pdf.cell(ln=1, h=10.0, align='L', w=0, txt=f"Nilai Axle Load Total : {int(dt_load_total_value)} kg")
            pdf.cell(ln=1, h=10.0, align='L', w=0, txt=f"Status Pengujian Axle Load: {'Lulus' if dt_load_flag == 2 else 'Tidak Lulus' if dt_load_flag == 1 else 'Belum Diuji'}")
            pdf.cell(ln=1, h=5.0, w=0)

            pdf.cell(ln=1, h=10.0, align='L', w=80, txt=f"REM UTAMA")
            pdf.cell(ln=0, h=10.0, align='L', w=80, txt=f"No. Sumbu")
            pdf.cell(ln=0, h=10.0, align='L', w=80, txt=f"Kiri")
            pdf.cell(ln=0, h=10.0, align='L', w=80, txt=f"Kanan")
            pdf.cell(ln=0, h=10.0, align='L', w=80, txt=f"Total")
            pdf.cell(ln=1, h=10.0, align='L', w=80, txt=f"Selisih")
            for i in range(10):
                if (db_load_total_value[i] > 0):
                    pdf.cell(ln=0, h=10.0, align='L', w=80, txt=f"S{i+1}")
                    pdf.cell(ln=0, h=10.0, align='L', w=80, txt=f"{int(db_brake_left_value[i])} kg")
                    pdf.cell(ln=0, h=10.0, align='L', w=80, txt=f"{int(db_brake_right_value[i])} kg")
                    pdf.cell(ln=0, h=10.0, align='L', w=80, txt=f"{int(db_brake_total_value[i])} kg")
                    pdf.cell(ln=1, h=10.0, align='L', w=80, txt=f"{int(db_brake_difference_value[i])} kg")
            pdf.cell(ln=1, h=10.0, align='L', w=0, txt=f"Nilai Rem Utama Total : {int(dt_brake_total_value)} kg")
            pdf.cell(ln=1, h=10.0, align='L', w=0, txt=f"Nilai Efisiensi Rem Utama : {str(np.round(dt_brake_efficiency_value, 1)).replace('.', ',')} %")
            pdf.cell(ln=1, h=10.0, align='L', w=0, txt=f"Status Pengujian Rem Utama: {'Lulus' if dt_brake_flag == 2 else 'Tidak Lulus' if dt_brake_flag == 1 else 'Belum Diuji'}")
            pdf.cell(ln=1, h=5.0, w=0)

            pdf.cell(ln=1, h=10.0, align='L', w=80, txt=f"REM PARKIR")
            pdf.cell(ln=0, h=10.0, align='L', w=80, txt=f"No. Sumbu")
            pdf.cell(ln=0, h=10.0, align='L', w=80, txt=f"Kiri")
            pdf.cell(ln=0, h=10.0, align='L', w=80, txt=f"Kanan")
            pdf.cell(ln=0, h=10.0, align='L', w=80, txt=f"Total")
            for i in range(10):
                if (db_load_total_value[i] > 0):
                    pdf.cell(ln=0, h=10.0, align='L', w=80, txt=f"S{i+1}")
                    pdf.cell(ln=0, h=10.0, align='L', w=80, txt=f"{int(db_handbrake_left_value[i])} kg")
                    pdf.cell(ln=0, h=10.0, align='L', w=80, txt=f"{int(db_handbrake_right_value[i])} kg")
                    pdf.cell(ln=1, h=10.0, align='L', w=80, txt=f"{int(db_handbrake_total_value[i])} kg")

            pdf.cell(ln=1, h=10.0, align='L', w=0, txt=f"Nilai Rem Parkir Total : {int(dt_handbrake_total_value)} kg")
            pdf.cell(ln=1, h=10.0, align='L', w=0, txt=f"Nilai Efisiensi Rem Parkir : {str(np.round(dt_handbrake_efficiency_value, 1)).replace('.', ',')} %")
            pdf.cell(ln=1, h=10.0, align='L', w=0, txt=f"Status Pengujian Rem Parkir: {'Lulus' if dt_handbrake_flag == 2 else 'Tidak Lulus' if dt_handbrake_flag == 1 else 'Belum Diuji'}")

            pdf_path = os.path.join(os.path.join(os.environ["USERPROFILE"]), "Documents", f'Hasil_Uji_VIIS_AxleLoad_Brake_{str(time.strftime("%Y_%B_%d_%H_%M_%S", time.localtime()))}.pdf')
            pdf.output(pdf_path, 'F')
            os.startfile(pdf_path)

        except Exception as e:
            toast_msg = f'Gagal menyimpan ke pdf'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_print_thermal(self):
        global flag_play
        global count_starting, count_get_data
        global mydb, db_antrian
        global dt_no_antrian, dt_no_pol, dt_no_uji, dt_nama, dt_jenis_kendaraan
        global dt_load_flag, dt_brake_flag, dt_handbrake_flag
        global db_load_left_value, db_load_right_value, db_load_total_value
        global db_brake_left_value, db_brake_right_value, db_brake_total_value, db_brake_efficiency_value, db_brake_difference_value
        global db_handbrake_left_value, db_handbrake_right_value, db_handbrake_total_value, db_handbrake_efficiency_value, db_handbrake_difference_value
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
            printer.textln(" \n ")
            printer.textln("VEHICLE INSPECTION INTEGRATION SYSTEM")
            printer.textln("AXLE LOAD & BRAKE")
            printer.textln("================================================================")
            printer.text(f"No Antrian: {dt_no_antrian}\t")
            printer.text(f"No Reg: {dt_no_pol}\t")
            printer.textln(f"No Uji: {dt_no_uji}")
            printer.textln("  ")
            printer.text(f"Nama: {dt_nama}\t")
            printer.textln(f"Jenis Kendaraan: {dt_jenis_kendaraan}")
            printer.textln("  ")
            printer.textln(f"Tanggal: {print_datetime}")
            printer.textln("  ")
            printer.textln(f"AXLE LOAD")
            printer.text(f"No. Sumbu \tKiri \tKanan \tTotal")
            for i in range(10):
                if (db_load_total_value[i] > 0.0):
                    printer.textln(f"S{i+1} \t{db_load_left_value[i]} \t{db_load_right_value[i]} \t{db_load_total_value[i]}")
            printer.textln(f"Nilai Axle Load Total : {dt_load_total_value}")
            printer.textln(f"Status Pengujian Axle Load : {'Lulus' if dt_load_flag == 2 else 'Tidak Lulus' if dt_load_flag == 1 else 'Belum Diuji'}")
            printer.textln("  ")
            printer.textln(f"REM UTAMA")
            printer.text(f"No. Sumbu \tKiri \tKanan \tTotal \tSelisih")
            for i in range(10):
                if (db_load_total_value[i] > 0.0):
                    printer.textln(f"S{i+1} \t{db_brake_left_value[i]} \t{db_brake_right_value[i]} \t{db_brake_total_value[i]} \t{db_brake_difference_value[i]}")
            printer.textln(f"Nilai Rem Utama Total : {dt_brake_total_value}")
            printer.textln(f"Nilai Efisiensi Rem Utama : {dt_brake_efficiency_value}")
            printer.textln(f"Status Pengujian Rem : {'Lulus' if dt_brake_flag == 2 else 'Tidak Lulus' if dt_brake_flag == 1 else 'Belum Diuji'}")
            printer.textln("  ")            
            printer.textln(f"REM PARKIR")
            printer.text(f"No. Sumbu \tKiri \tKanan \tTotal")
            for i in range(10):
                if (db_load_total_value[i] > 0.0):
                    printer.textln(f"S{i+1} \t{db_handbrake_left_value[i]} \t{db_handbrake_right_value[i]} \t{db_handbrake_total_value[i]}")
            printer.textln(f"Nilai Rem Parkir Total : {dt_handbrake_total_value}")
            printer.textln(f"Nilai Efisiensi Rem Parkir : {dt_handbrake_efficiency_value}")
            printer.textln(f"Status Pengujian Rem Parkir : {'Lulus' if dt_handbrake_flag == 2 else 'Tidak Lulus' if dt_handbrake_flag == 1 else 'Belum Diuji'}")
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
        self.theme_cls.colors = colors
        self.theme_cls.primary_palette = "Gray"
        self.theme_cls.accent_palette = "Blue"
        self.theme_cls.theme_style = "Light"
        self.icon = 'assets/images/logo-load-app.png'
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
