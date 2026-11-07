import pandas as pd

from Applicación.datos import generar_datos_sinteticos, anonimizar_dataset

def test_calidad_datos_sinteticos():
    """QA: Verifica que los datos sintéticos tengan el formato y los rangos correctos."""
    df = generar_datos_sinteticos(50)
    
    # Validar que no hay valores nulos generados por error
    assert df.isnull().sum().sum() == 0, "Fallo QA: Hay valores nulos en los datos generados."
    
    # Validar rangos de edad (Regla de negocio)
    assert df['edad'].min() >= 18, "Fallo QA: Se han generado datos de menores de edad."
    assert 'id_usuario' in df.columns, "Fallo QA: Falta el identificador en el esquema."

def test_anonimizacion_segura():
    """QA: Verifica que el hasheo destruye el dato original."""
    datos_prueba = pd.DataFrame({
        'email': ['usuario@uab.cat', 'test@uab.cat'],
        'edad': [22, 25]
    })
    
    df_anonimizado = anonimizar_dataset(datos_prueba, ['email'])
    
    # Verificamos que el email original ya no existe en la tabla
    assert df_anonimizado['email'].iloc[0] != 'usuario@uab.cat', "Fallo Privacidad: El email está en texto plano."
    # Verificamos que se haya hasheado (longitud de SHA-256 es 64 caracteres)
    assert len(df_anonimizado['email'].iloc[0]) == 64, "Fallo Privacidad: El hash no tiene el formato correcto."