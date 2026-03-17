from AlgorithmImports import *

class BotCriptoBlindado(QCAlgorithm):

    def initialize(self):
        self.set_start_date(2023, 1, 1)
        self.set_cash(100000)
        self.set_brokerage_model(BrokerageName.BITFINEX, AccountType.CASH)
        
        self.tickers = ["BTCUSD", "ETHUSD", "SOLUSD"]
        self.datos = {}
        
        # Parámetro del Trailing Stop (5%)
        self.trailing_pct = 0.05

        for ticker in self.tickers:
            simbolo = self.add_crypto(ticker, Resolution.Daily).symbol
            self.datos[simbolo] = {
                "fast": self.SMA(simbolo, 10, Resolution.Daily),
                "slow": self.SMA(simbolo, 30, Resolution.Daily),
                "max_price": 0  # Acá guardamos el pico más alto
            }
        
        self.peso = 1.0 / len(self.tickers)
        self.set_warm_up(30, Resolution.Daily)

    def on_data(self, data):
        if self.is_warming_up:
            return

        for simbolo, info in self.datos.items():
            if not data.contains_key(simbolo) or data[simbolo] is None:
                continue
            
            precio_actual = data[simbolo].close
            invested = self.portfolio[simbolo].invested

            # 1. Si NO estamos invertidos, buscamos el cruce de oro
            if not invested:
                if info["fast"].current.value > info["slow"].current.value:
                    self.set_holdings(simbolo, self.peso)
                    # Seteamos el precio máximo inicial al comprar
                    info["max_price"] = precio_actual
            
            # 2. Si YA estamos invertidos, gestionamos la salida
            else:
                # Actualizamos el precio máximo si el precio actual es mayor
                if precio_actual > info["max_price"]:
                    info["max_price"] = precio_actual
                
                # CÁLCULO DEL TRAILING STOP:
                # Si el precio actual cayó más del 5% desde el máximo... ¡AFUERA!
                if precio_actual < (info["max_price"] * (1 - self.trailing_pct)):
                    self.liquidate(simbolo)
                    info["max_price"] = 0 # Reseteamos para la próxima
                    self.debug(f"TRAILING STOP en {simbolo}: Protegiendo ganancias.")

                # También salimos si hay cruce bajista de medias
                elif info["fast"].current.value < info["slow"].current.value:
                    self.liquidate(simbolo)
                    info["max_price"] = 0