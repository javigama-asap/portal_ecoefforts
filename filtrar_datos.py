import json

# 1. Cargar el archivo original
try:
    with open('datos_completos.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
except FileNotFoundError:
    print("Error: No se encuentra el archivo 'datos_completos.json'")
    exit()

# 2. Definir las apps que queremos rescatar
apps_validas = ('ajustes', 'logistica')

# 3. Filtrar los datos
datos_filtrados = [
    item for item in data 
    if item['model'].split('.')[0] in apps_validas
]

# 4. Guardar el resultado limpio
with open('importar_limpio.json', 'w', encoding='utf-8') as f:
    json.dump(datos_filtrados, f, indent=4, ensure_ascii=False)

print(f"Éxito: Se han extraído {len(datos_filtrados)} registros de ajustes y logistica.")
print("Archivo creado: importar_limpio.json")