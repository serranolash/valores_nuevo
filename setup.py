from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": ["flask"],  # Añade todos los paquetes necesarios de Flask
    "include_files": ["templates"],  # Incluye directorios de templates y static
}

setup(
    name="ApiDragon",
    version="1.0",
    description="Descripción de tu aplicación",
    options={"build_exe": build_exe_options},
    executables=[Executable("app.py", base="Console")]
)
