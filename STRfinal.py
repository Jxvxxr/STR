import machine
import time
import uasyncio as asyncio
from machine import Pin, PWM

class FiltroPasaBajo:
    def __init__(self, frecuencia_corte, periodo_muestreo):
        self.alpha = 2 * 3.14159 * frecuencia_corte * periodo_muestreo / (2 * 3.14159 * frecuencia_corte * periodo_muestreo + 1)
        self.y_prev = 0
    
    def filtrar(self, x):
        y = (1 - self.alpha) * self.y_prev + self.alpha * x
        self.y_prev = y
        return y

pot_value = machine.ADC(26)
analog_value = machine.ADC(27)
conversion_factor = 3.3 / 65535
servo = PWM(Pin(16))
servo.freq(50)

TIP31 = PWM(Pin(17))
TIP31.freq(50)
LED = PWM(Pin(18))
LED.freq(50)

shared_data = {'tempC': 0, 'lectura_potenciometro_filtrada': 0}
mutex = asyncio.Lock()

frecuencia_corte_potenciometro = 338.6275
periodo_muestreo_potenciometro = 0.002
filtro_potenciometro = FiltroPasaBajo(frecuencia_corte_potenciometro, periodo_muestreo_potenciometro)


async def lecturaLM35():
    while True:
        temp_voltage_raw = analog_value.read_u16()
        convert_voltage = temp_voltage_raw * conversion_factor
        tempC = convert_voltage / (1.0 / 1000)
        async with mutex:
            shared_data['tempC'] = tempC
        print("Temperatura:", tempC, "C", sep="")
        await asyncio.sleep(2)
        

async def Servomotor():
    while True:
        async with mutex:
            tempC = shared_data['tempC']
        if tempC < 30:
            print("Frio")
            servo.duty_ns(500000)
            await asyncio.sleep_ms(500)
        elif tempC > 30:
            print("Caliente")
            servo.duty_ns(2500000)
            await asyncio.sleep_ms(500)
        await asyncio.sleep(2)
        await asyncio.sleep(0)
        

async def lecturaPotenciometro():
    while True:
        lectura_potenciometro_raw = pot_value.read_u16()
        lectura_potenciometro = lectura_potenciometro_raw * conversion_factor
        lectura_potenciometro_filtrada = filtro_potenciometro.filtrar(lectura_potenciometro)
        async with mutex:
            shared_data['lectura_potenciometro_filtrada'] = lectura_potenciometro_filtrada
        print("Lectura Potenciómetro (original):", lectura_potenciometro)
        print("Lectura Potenciómetro (filtrada):", lectura_potenciometro_filtrada)
        await asyncio.sleep(2)
        

async def TIP31t():
    while True:
        async with mutex:
            lectura_potenciometro_filtrada = shared_data['lectura_potenciometro_filtrada']
        if 0.000 < lectura_potenciometro_filtrada < 1.5:
            TIP31.duty_ns(1200000)
            LED.duty_ns(1200000)
            print("Nivel bajo 25%")
        elif 1.5 <= lectura_potenciometro_filtrada <= 3.0:
            TIP31.duty_ns(500000)
            LED.duty_ns(500000)
            print("Nivel alto 60%")
        await asyncio.sleep(2)
        await asyncio.sleep(0)
        
        #TIP31.duty_ns(600000000)
        #LED.duty_ns(600000000)
        #print("Nivel alto 60%")

        

        
        

tarea_1 = lecturaLM35()
tarea_2 = Servomotor()
tarea_3 = lecturaPotenciometro()
tarea_4 = TIP31t()

loop = asyncio.get_event_loop()
loop.create_task(tarea_1)
loop.create_task(tarea_2)
loop.create_task(tarea_3)
loop.create_task(tarea_4)
loop.run_forever()

