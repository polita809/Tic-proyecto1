import time
import random
import board
import busio
import adafruit_dht
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from gpiozero import TonalBuzzer, RGBLED, Button

# ============================================================
# ZONA SAFARI POKEMON - MINI PROYECTO 1
# Hardware:
# DHT11 -> GPIO 4
# ADS1115 -> I2C (SCL/SDA)
# Joystick KY-023 -> VRx ADS A0, VRy ADS A1, SW GPIO 17
# Buzzer pasivo KY-006 -> GPIO 27
# LED RGB 1 -> GPIO 24,23,22
# LED RGB 2 -> GPIO 5,6,12
# ============================================================

# -------------------- HARDWARE --------------------
dht = adafruit_dht.DHT11(board.D4)

i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)

joy_x = AnalogIn(ads, ADS.P0)  # VRx
joy_y = AnalogIn(ads, ADS.P1)  # VRy
joy_btn = Button(17, pull_up=True)

buzzer = TonalBuzzer(27)
led_radar = RGBLED(red=24, green=23, blue=22)
led_eventos = RGBLED(red=5, green=6, blue=12)

# -------------------- POKEMON --------------------
equipo_jugador = []

habitats = {
    "Bosque": [
        {"nombre": "Bulbasaur", "tipo": "Planta", "hp_max": 45, "prob_captura": 45, "cantidad": 3,
         "ataques": [{"nombre": "Placaje", "daño": 10}, {"nombre": "Hoja Afilada", "daño": 15}]},
        {"nombre": "Oddish", "tipo": "Planta", "hp_max": 45, "prob_captura": 60, "cantidad": 2,
         "ataques": [{"nombre": "Absorber", "daño": 10}, {"nombre": "Ácido", "daño": 12}]},
        {"nombre": "Caterpie", "tipo": "Bicho", "hp_max": 45, "prob_captura": 80, "cantidad": 1,
         "ataques": [{"nombre": "Placaje", "daño": 10}, {"nombre": "Picotazo", "daño": 5}]}
    ],
    "Playa": [
        {"nombre": "Squirtle", "tipo": "Agua", "hp_max": 44, "prob_captura": 45, "cantidad": 2,
         "ataques": [{"nombre": "Pistola Agua", "daño": 15}, {"nombre": "Placaje", "daño": 10}]},
        {"nombre": "Krabby", "tipo": "Agua", "hp_max": 30, "prob_captura": 60, "cantidad": 3,
         "ataques": [{"nombre": "Burbuja", "daño": 10}, {"nombre": "Agarre", "daño": 14}]},
        {"nombre": "Dewott", "tipo": "Agua", "hp_max": 75, "prob_captura": 35, "cantidad": 1,
         "ataques": [{"nombre": "Torrente", "daño": 20}, {"nombre": "Pistola Agua", "daño": 15}]}
    ],
    "Volcán": [
        {"nombre": "Charmander", "tipo": "Fuego", "hp_max": 39, "prob_captura": 45, "cantidad": 2,
         "ataques": [{"nombre": "Ascuas", "daño": 15}, {"nombre": "Arañazo", "daño": 10}]},
        {"nombre": "Vulpix", "tipo": "Fuego", "hp_max": 38, "prob_captura": 55, "cantidad": 2,
         "ataques": [{"nombre": "Giro Fuego", "daño": 12}, {"nombre": "Ataque Rápido", "daño": 10}]},
        {"nombre": "Growlithe", "tipo": "Fuego", "hp_max": 55, "prob_captura": 40, "cantidad": 1,
         "ataques": [{"nombre": "Rueda de Fuego", "daño": 18}, {"nombre": "Morder", "daño": 12}]}
    ],
    "Ciudad": [
        {"nombre": "Pikachu", "tipo": "Eléctrico", "hp_max": 35, "prob_captura": 40, "cantidad": 1,
         "ataques": [{"nombre": "Impactrueno", "daño": 16}, {"nombre": "Ataque Rápido", "daño": 10}]},
        {"nombre": "Rattata", "tipo": "Normal", "hp_max": 30, "prob_captura": 75, "cantidad": 3,
         "ataques": [{"nombre": "Placaje", "daño": 10}, {"nombre": "Mordisco", "daño": 12}]},
        {"nombre": "Meowth", "tipo": "Normal", "hp_max": 40, "prob_captura": 60, "cantidad": 2,
         "ataques": [{"nombre": "Arañazo", "daño": 10}, {"nombre": "Golpes Furiosos", "daño": 14}]}
    ]
}

# Triángulo mínimo pedido por la pauta:
# Fuego > Planta > Agua > Fuego
efectividad = {
    "Fuego": {"Planta": 2.0, "Agua": 0.5, "Fuego": 0.5},
    "Agua": {"Fuego": 2.0, "Planta": 0.5, "Agua": 0.5},
    "Planta": {"Agua": 2.0, "Fuego": 0.5, "Planta": 0.5}
}

# Varias historias por hábitat para Descansar.
historias = {
    "Bosque": [
        "Te sientas bajo un árbol y escuchas hojas moverse entre la vegetación.",
        "Una pequeña corriente de aire atraviesa el bosque mientras descansas.",
        "Encuentras algunas bayas silvestres cerca de un tronco cubierto de musgo."
    ],
    "Playa": [
        "Te sientas cerca de la orilla y escuchas el sonido de las olas.",
        "Una brisa marina refresca el ambiente mientras recuperas energías.",
        "Ves huellas de Pokémon cerca de la arena y decides observarlas un momento."
    ],
    "Volcán": [
        "Encuentras una zona segura entre las rocas y descansas lejos del calor intenso.",
        "El suelo tibio y el resplandor de las rocas volcánicas acompañan tu descanso.",
        "Una corriente de aire caliente atraviesa el paisaje mientras exploras con cuidado."
    ],
    "Ciudad": [
        "Te detienes en una plaza y observas a los Pokémon que recorren la ciudad.",
        "Descansas junto a una banca mientras escuchas los sonidos de la ciudad.",
        "Una calle tranquila te permite recuperar energías antes de continuar."
    ]
}

# -------------------- SONIDOS INDIVIDUALES --------------------
# Son "cries" electrónicos distintos para cada Pokémon, hechos con el
# buzzer pasivo. Para reproducir audios reales se necesitaría un parlante
# y archivos de audio, no solo el KY-006.
sonidos_pokemon = {
    "Bulbasaur": ["C4", "E4", "G4"],
    "Oddish": ["G4", "E4", "C4"],
    "Caterpie": ["E5", "G5", "E5"],
    "Squirtle": ["C4", "G4", "C5"],
    "Krabby": ["A4", "C5", "A4"],
    "Dewott": ["D4", "F4", "A4"],
    "Charmander": ["E4", "G4", "B4"],
    "Vulpix": ["G4", "B4", "D5"],
    "Growlithe": ["C4", "E4", "C5"],
    "Pikachu": ["E5", "G5", "E5", "C5"],
    "Rattata": ["A4", "E4", "A4"],
    "Meowth": ["D5", "B4", "D5"]
}

def reproducir_notas(notas, duracion=0.10, pausa=0.04):
    for nota in notas:
        try:
            buzzer.play(nota)
            time.sleep(duracion)
            buzzer.stop()
            time.sleep(pausa)
        except Exception:
            buzzer.stop()

def sonido_movimiento():
    reproducir_notas(["C5"], 0.05, 0)

def sonido_seleccion():
    reproducir_notas(["C5", "G5"], 0.07, 0.03)

def sonido_aparicion(pokemon):
    led_eventos.color = (0.2, 0.2, 1)
    reproducir_notas(sonidos_pokemon[pokemon["nombre"]], 0.09, 0.03)
    led_eventos.off()

def sonido_comida():
    led_eventos.color = (1, 0.7, 0)
    reproducir_notas(["E4", "G4", "B4"], 0.08, 0.03)
    led_eventos.off()

def sonido_captura_exitosa():
    led_eventos.color = (0, 1, 0)
    reproducir_notas(["C5", "E5", "G5", "C6"], 0.10, 0.04)
    led_eventos.off()

def sonido_captura_fallida():
    led_eventos.color = (1, 0, 0)
    reproducir_notas(["G4", "E4"], 0.16, 0.05)
    led_eventos.off()

def sonido_escape():
    led_eventos.color = (0.7, 0, 1)
    reproducir_notas(["E5", "C5"], 0.08, 0.04)
    led_eventos.off()

def sonido_ataque_efectivo():
    led_eventos.color = (0, 1, 1)
    reproducir_notas(["G5", "C6"], 0.10, 0.04)
    led_eventos.off()

def sonido_ataque_neutral():
    reproducir_notas(["E4"], 0.08, 0)

def sonido_ataque_poco_efectivo():
    led_eventos.color = (1, 0.5, 0)
    reproducir_notas(["E4", "C4"], 0.12, 0.04)
    led_eventos.off()

def sonido_victoria():
    led_eventos.color = (0, 1, 0)
    reproducir_notas(["C5", "E5", "G5", "C6"], 0.13, 0.05)
    led_eventos.off()

def sonido_derrota():
    led_eventos.color = (1, 0, 0)
    reproducir_notas(["C4", "B3", "G3"], 0.18, 0.06)
    led_eventos.off()

def sonido_debilitamiento():
    led_eventos.color = (1, 0.3, 0)
    reproducir_notas(["G4", "E4", "C4"], 0.14, 0.05)
    led_eventos.off()

def sonido_captura_post_combate():
    led_eventos.color = (0, 1, 0.5)
    reproducir_notas(["G4", "C5", "E5", "G5"], 0.11, 0.05)
    led_eventos.off()

# -------------------- SENSOR Y JOYSTICK --------------------
ultima_temp = 22
ultima_hum = 50

def obtener_clima():
    global ultima_temp, ultima_hum
    try:
        temp = dht.temperature
        hum = dht.humidity
        if temp is not None:
            ultima_temp = temp
        if hum is not None:
            ultima_hum = hum
    except Exception:
        pass
    return ultima_temp, ultima_hum

def leer_joystick():
    # VRy se usa para arriba/abajo.
    # VRx también se lee mediante ADS1115, aunque el menú principal
    # utiliza VRy como eje principal de navegación.
    _val_x = joy_x.value
    val_y = joy_y.value

    if joy_btn.is_pressed:
        return "SELECCIONAR"

    if val_y < 10000:
        return "ARRIBA"
    if val_y > 22000:
        return "ABAJO"

    return "CENTRO"

def limpiar_pantalla():
    print("\n" * 5)

def menu_interactivo(opciones, titulo="SELECCIONA UNA OPCIÓN"):
    indice = 0

    while True:
        limpiar_pantalla()
        print("=" * 52)
        print(f"{titulo:^52}")
        print("=" * 52)

        for i, opcion in enumerate(opciones):
            if i == indice:
                print(f"  >>> {opcion}")
            else:
                print(f"      {opcion}")

        print("\nJoystick: arriba/abajo | Botón: seleccionar")

        accion = leer_joystick()

        if accion == "ABAJO":
            indice = (indice + 1) % len(opciones)
            sonido_movimiento()
            time.sleep(0.25)
        elif accion == "ARRIBA":
            indice = (indice - 1) % len(opciones)
            sonido_movimiento()
            time.sleep(0.25)
        elif accion == "SELECCIONAR":
            sonido_seleccion()
            time.sleep(0.25)
            return indice

        time.sleep(0.08)

def esperar_boton(titulo="CONTINUAR"):
    menu_interactivo([titulo], titulo)

# -------------------- POBLACIÓN Y LED RADAR --------------------
def pokemon_base(nombre, habitat):
    for p in habitats[habitat]:
        if p["nombre"] == nombre:
            return p
    return None

def disminuir_poblacion(nombre, habitat):
    p = pokemon_base(nombre, habitat)
    if p is not None and p["cantidad"] > 0:
        p["cantidad"] -= 1

def poblacion_habitat(habitat):
    return sum(p["cantidad"] for p in habitats[habitat])

def actualizar_led_radar(habitat):
    if poblacion_habitat(habitat) > 0:
        led_radar.color = (0, 0, 1)
    else:
        led_radar.off()

# -------------------- HÁBITATS SEGÚN AMBIENTE --------------------
def habitats_disponibles(temp, hum):
    disponibles = []

    # Dos hábitats definidos principalmente por TEMPERATURA.
    if temp >= 27:
        disponibles.append("Volcán")
    if temp <= 20:
        disponibles.append("Ciudad")

    # Dos hábitats definidos principalmente por HUMEDAD.
    if hum >= 60:
        disponibles.append("Bosque")
    if hum < 60:
        disponibles.append("Playa")

    return [h for h in habitats if h in disponibles]

# -------------------- EQUIPO --------------------
def copiar_para_equipo(pokemon):
    nuevo = dict(pokemon)
    nuevo["hp_actual"] = nuevo["hp_max"]
    nuevo["ataques"] = [dict(a) for a in pokemon["ataques"]]
    return nuevo

def agregar_a_equipo(pokemon, post_combate=False):
    if len(equipo_jugador) < 6:
        nuevo = copiar_para_equipo(pokemon)
        equipo_jugador.append(nuevo)

        if post_combate:
            print(f"\n¡{pokemon['nombre']} fue incorporado después del combate!")
            sonido_captura_post_combate()
        else:
            print(f"\n¡{pokemon['nombre']} se unió a tu equipo!")
            sonido_captura_exitosa()

        time.sleep(1.5)
        return True

    # Equipo lleno: la pauta exige "Liberar y capturar" o "Retirarse".
    opciones = ["Liberar y capturar", "Retirarse"]
    idx = menu_interactivo(opciones, "EQUIPO COMPLETO")

    if idx == 1:
        print(f"\nTe retiraste. {pokemon['nombre']} no fue incorporado.")
        sonido_escape()
        time.sleep(1.5)
        return False

    nombres = [
        f"{p['nombre']} (HP {p['hp_actual']}/{p['hp_max']})"
        for p in equipo_jugador
    ]
    idx_liberar = menu_interactivo(nombres, "ELIGE A QUIÉN LIBERAR")

    liberado = equipo_jugador.pop(idx_liberar)
    nuevo = copiar_para_equipo(pokemon)
    equipo_jugador.append(nuevo)

    print(f"\nLiberaste a {liberado['nombre']} y capturaste a {pokemon['nombre']}.")
    if post_combate:
        sonido_captura_post_combate()
    else:
        sonido_captura_exitosa()
    time.sleep(1.5)
    return True

def mostrar_equipo():
    limpiar_pantalla()
    print("=" * 52)
    print("                    MI EQUIPO")
    print("=" * 52)

    if not equipo_jugador:
        print("Todavía no tienes Pokémon.")
    else:
        for i, p in enumerate(equipo_jugador, 1):
            print(
                f"{i}. {p['nombre']} | Tipo: {p['tipo']} | "
                f"HP: {p['hp_actual']}/{p['hp_max']}"
            )

    esperar_boton()

# -------------------- POKÉDEX --------------------
def ficha_pokemon(pokemon, habitat):
    limpiar_pantalla()
    print("=" * 52)
    print("                    POKÉDEX")
    print("=" * 52)
    print(f"Nombre:       {pokemon['nombre']}")
    print(f"Tipo:         {pokemon['tipo']}")
    print(f"Hábitat:      {habitat}")
    print(f"HP máximo:    {pokemon['hp_max']}")
    print(f"Captura base: {pokemon['prob_captura']}%")
    print(f"Cantidad:     {pokemon['cantidad']}")
    print(f"Ataque 1:     {pokemon['ataques'][0]['nombre']} "
          f"({pokemon['ataques'][0]['daño']} daño)")
    print(f"Ataque 2:     {pokemon['ataques'][1]['nombre']} "
          f"({pokemon['ataques'][1]['daño']} daño)")
    if pokemon["cantidad"] == 0:
        print("\nESTADO: POBLACIÓN AGOTADA")

    esperar_boton("Volver a la Pokédex")

def mostrar_pokedex(habitat):
    actualizar_led_radar(habitat)

    while True:
        opciones = [p["nombre"] for p in habitats[habitat]]
        opciones.append("Volver")

        idx = menu_interactivo(opciones, f"POKÉDEX - {habitat.upper()}")

        if idx == len(opciones) - 1:
            return

        ficha_pokemon(habitats[habitat][idx], habitat)

# -------------------- DESCANSAR --------------------
def descansar(habitat):
    limpiar_pantalla()
    print("=" * 52)
    print("                    DESCANSAR")
    print("=" * 52)
    print("\n" + random.choice(historias[habitat]))
    esperar_boton()

# -------------------- CAPTURA --------------------
def encuentro_captura(wild_pokemon, habitat):
    prob = wild_pokemon["prob_captura"]

    limpiar_pantalla()
    print("=" * 52)
    print(f"¡UN {wild_pokemon['nombre'].upper()} SALVAJE APARECIÓ!")
    print("=" * 52)
    print(f"Tipo: {wild_pokemon['tipo']} | HP: {wild_pokemon['hp_max']}")
    print(f"Probabilidad base de captura: {prob}%")

    # Sonido individual del Pokémon.
    sonido_aparicion(wild_pokemon)
    time.sleep(0.8)

    while True:
        opciones = [
            f"Lanzar Poké Ball ({prob}%)",
            "Dar de comer (+15%)",
            "Escapar"
        ]
        idx = menu_interactivo(opciones, f"ENCUENTRO: {wild_pokemon['nombre'].upper()}")

        if idx == 0:
            resultado = random.randint(1, 100)

            if resultado <= prob:
                disminuir_poblacion(wild_pokemon["nombre"], habitat)
                print(f"\n¡Capturaste a {wild_pokemon['nombre']}!")
                agregar_a_equipo(wild_pokemon)
                time.sleep(1)
                return

            print(f"\nLa Poké Ball falló. Probabilidad actual: {prob}%.")
            sonido_captura_fallida()

            if random.random() < 0.40:
                print(f"\n¡{wild_pokemon['nombre']} huyó!")
                sonido_escape()
                time.sleep(1.2)
                return

            esperar_boton("Intentar nuevamente")

        elif idx == 1:
            prob = min(100, prob + 15)
            print(f"\nLe diste comida a {wild_pokemon['nombre']}.")
            print(f"Probabilidad de captura ahora: {prob}%")
            sonido_comida()
            esperar_boton()

        else:
            print(f"\nEscapaste del encuentro con {wild_pokemon['nombre']}.")
            sonido_escape()
            time.sleep(1.2)
            return

# -------------------- COMBATE --------------------
def multiplicador(tipo_atacante, tipo_defensor):
    return efectividad.get(tipo_atacante, {}).get(tipo_defensor, 1.0)

def seleccionar_pokemon_equipo():
    opciones = [
        f"{p['nombre']} | HP {p['hp_actual']}/{p['hp_max']}"
        for p in equipo_jugador
    ]
    return menu_interactivo(opciones, "ELIGE TU POKÉMON")

def turno_jugador(mi_pokemon, wild_pokemon):
    limpiar_pantalla()
    print("=" * 52)
    print(f"POKÉMON ACTIVO: {mi_pokemon['nombre']}")
    print(f"HP: {mi_pokemon['hp_actual']}/{mi_pokemon['hp_max']}")
    print("=" * 52)
    print(f"Enemigo: {wild_pokemon['nombre']} | "
          f"HP: {wild_pokemon['hp_actual']}/{wild_pokemon['hp_max']}")
    print("\nAtaques disponibles:")

    opciones = [
        f"{a['nombre']} ({a['daño']} daño)"
        for a in mi_pokemon["ataques"]
    ]

    idx = menu_interactivo(opciones, f"TURNO DE {mi_pokemon['nombre'].upper()}")
    ataque = mi_pokemon["ataques"][idx]

    mult = multiplicador(mi_pokemon["tipo"], wild_pokemon["tipo"])
    daño = max(1, int(ataque["daño"] * mult))
    wild_pokemon["hp_actual"] -= daño

    print(f"\n{mi_pokemon['nombre']} usó {ataque['nombre']}.")

    if mult == 2.0:
        print("¡Es súper efectivo! x2")
        sonido_ataque_efectivo()
    elif mult == 0.5:
        print("No es muy efectivo... x0.5")
        sonido_ataque_poco_efectivo()
    else:
        print("Daño neutral. x1")
        sonido_ataque_neutral()

    print(f"Causaste {daño} de daño.")
    time.sleep(1.2)

def turno_salvaje(mi_pokemon, wild_pokemon):
    ataque = random.choice(wild_pokemon["ataques"])
    mult = multiplicador(wild_pokemon["tipo"], mi_pokemon["tipo"])
    daño = max(1, int(ataque["daño"] * mult))
    mi_pokemon["hp_actual"] -= daño

    print(f"\n{wild_pokemon['nombre']} usó {ataque['nombre']}.")
    if mult == 2.0:
        print("¡El ataque salvaje fue súper efectivo! x2")
    elif mult == 0.5:
        print("El ataque salvaje fue poco efectivo. x0.5")
    else:
        print("Daño neutral. x1")

    print(f"Recibiste {daño} de daño.")
    time.sleep(1.2)

def captura_post_combate(wild_pokemon):
    idx = menu_interactivo(
        ["Capturar", "Retirarse"],
        f"¿QUÉ HACER CON {wild_pokemon['nombre'].upper()}?"
    )

    if idx == 1:
        print(f"\nTe retiraste y dejaste ir a {wild_pokemon['nombre']}.")
        sonido_escape()
        time.sleep(1.2)
        return

    agregar_a_equipo(wild_pokemon, post_combate=True)

def encuentro_combate(wild_pokemon, habitat):
    # Copia independiente: el HP del ejemplar salvaje no modifica la base.
    wild_pokemon = dict(wild_pokemon)
    wild_pokemon["ataques"] = [dict(a) for a in wild_pokemon["ataques"]]
    wild_pokemon["hp_actual"] = wild_pokemon["hp_max"]

    limpiar_pantalla()
    print("=" * 52)
    print(f"¡COMBATE CONTRA {wild_pokemon['nombre'].upper()}!")
    print("=" * 52)
    sonido_aparicion(wild_pokemon)
    time.sleep(0.7)

    indice_equipo = seleccionar_pokemon_equipo()

    while equipo_jugador:
        if indice_equipo >= len(equipo_jugador):
            indice_equipo = 0

        mi_pokemon = equipo_jugador[indice_equipo]

        if mi_pokemon["hp_actual"] <= 0:
            equipo_jugador.pop(indice_equipo)
            sonido_debilitamiento()
            continue

        # Turno del jugador.
        turno_jugador(mi_pokemon, wild_pokemon)

        if wild_pokemon["hp_actual"] <= 0:
            print(f"\n¡{wild_pokemon['nombre']} fue debilitado!")
            disminuir_poblacion(wild_pokemon["nombre"], habitat)
            wild_pokemon["hp_actual"] = wild_pokemon["hp_max"]

            print("\n¡VICTORIA!")
            sonido_victoria()
            time.sleep(1.2)

            # La captura posterior al combate tiene su propio flujo.
            captura_post_combate(wild_pokemon)
            return

        # Turno aleatorio del Pokémon salvaje.
        turno_salvaje(mi_pokemon, wild_pokemon)

        if mi_pokemon["hp_actual"] <= 0:
            print(f"\n¡{mi_pokemon['nombre']} llegó a 0 HP!")
            print("Queda debilitado permanentemente (Nuzlocke).")
            equipo_jugador.pop(indice_equipo)
            sonido_debilitamiento()
            time.sleep(1.2)

            if not equipo_jugador:
                print("\n¡DERROTA! No quedan Pokémon en tu equipo.")
                sonido_derrota()
                esperar_boton("Volver al hábitat")
                return

            # Si quedan integrantes, se elige uno nuevo.
            indice_equipo = seleccionar_pokemon_equipo()

# -------------------- PRÓXIMA AVENTURA --------------------
def proxima_aventura(habitat):
    disponibles = [p for p in habitats[habitat] if p["cantidad"] > 0]

    # Si se agotó la población del hábitat, todavía se puede descansar.
    if not disponibles:
        descansar(habitat)
        return

    eventos = ["Descansar", "Atrapar"]

    # Combatir solo existe después de capturar al menos un Pokémon.
    if equipo_jugador:
        eventos.append("Combatir")

    # La pauta exige que cada aventura escoja aleatoriamente el evento.
    evento = random.choice(eventos)

    limpiar_pantalla()
    print("=" * 52)
    print("               PRÓXIMA AVENTURA")
    print("=" * 52)
    print(f"\nEl evento elegido al azar es: {evento}")
    time.sleep(1)

    if evento == "Descansar":
        descansar(habitat)

    elif evento == "Atrapar":
        wild_pokemon = dict(random.choice(disponibles))
        wild_pokemon["ataques"] = [dict(a) for a in wild_pokemon["ataques"]]
        encuentro_captura(wild_pokemon, habitat)

    elif evento == "Combatir":
        wild_pokemon = dict(random.choice(disponibles))
        wild_pokemon["ataques"] = [dict(a) for a in wild_pokemon["ataques"]]
        encuentro_combate(wild_pokemon, habitat)

# -------------------- MENÚ DE HÁBITAT --------------------
def menu_habitat(habitat):
    while True:
        actualizar_led_radar(habitat)

        opciones = [
            "Ver Pokédex del hábitat",
            "Próxima aventura",
            "Ver mi equipo",
            "Volver"
        ]

        idx = menu_interactivo(opciones, f"HÁBITAT: {habitat.upper()}")

        if idx == 0:
            mostrar_pokedex(habitat)
        elif idx == 1:
            proxima_aventura(habitat)
        elif idx == 2:
            mostrar_equipo()
        else:
            led_radar.off()
            return

# -------------------- MENÚ PRINCIPAL --------------------
def menu_principal():
    indice = 0

    while True:
        temp, hum = obtener_clima()
        disponibles = habitats_disponibles(temp, hum)

        # Se muestran las zonas habilitadas por el ambiente + equipo + salir.
        opciones = disponibles + ["Ver mi equipo", "Salir"]

        if indice >= len(opciones):
            indice = 0

        if indice < len(disponibles):
            actualizar_led_radar(disponibles[indice])
        else:
            led_radar.off()

        limpiar_pantalla()
        print("=" * 52)
        print("             ZONA SAFARI POKÉMON")
        print("=" * 52)
        print(f"Temperatura: {temp} °C")
        print(f"Humedad:     {hum} %")
        print("\nZonas disponibles:")

        for i, opcion in enumerate(opciones):
            marcador = ">>>" if i == indice else "   "
            print(f"{marcador} {opcion}")

        print("\nJoystick: arriba/abajo | Botón: seleccionar")

        accion = leer_joystick()

        if accion == "ABAJO":
            indice = (indice + 1) % len(opciones)
            sonido_movimiento()
            time.sleep(0.25)

        elif accion == "ARRIBA":
            indice = (indice - 1) % len(opciones)
            sonido_movimiento()
            time.sleep(0.25)

        elif accion == "SELECCIONAR":
            sonido_seleccion()
            opcion = opciones[indice]
            time.sleep(0.25)

            if opcion == "Salir":
                limpiar_pantalla()
                print("¡Gracias por visitar la Zona Safari!")
                break

            elif opcion == "Ver mi equipo":
                mostrar_equipo()

            else:
                menu_habitat(opcion)

        time.sleep(0.08)

# -------------------- INICIO --------------------
if __name__ == "__main__":
    try:
        menu_principal()
    except KeyboardInterrupt:
        print("\nApagando Zona Safari...")
    finally:
        buzzer.stop()
        led_radar.off()
        led_eventos.off()
