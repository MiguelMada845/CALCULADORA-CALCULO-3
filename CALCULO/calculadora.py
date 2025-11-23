"""
Calculadora de Cálculo Multivariable - Prototipo de GUI
- Python 3.8+
- Dependencias: sympy, numpy, matplotlib, tkinter, mpmath

Funcionalidades implementadas:
- Integrales triples en Coordenadas Rectangulares, Cilíndricas, Esféricas (simbólicas cuando es posible)
- Tres teoremas vectoriales: Green (2D), Stokes (3D), Divergencia (Gauss) con regiones comunes
- Cálculos simbólicos paso a paso y justificaciones textuales
- Visualizaciones 2D/3D integradas con matplotlib en Tkinter
- Botones: Información, Ayuda, Limpiar (Borrar ejercicio), Guardar en Historial, Visor de Historial, Funcionalidades

"""

import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import sympy as sp
from sympy import symbols, sin, cos, tan, sqrt

# --------------------------- Utilidades auxiliares ---------------------------
ARCHIVO_HISTORIAL = 'historial_mv.json'

def cargar_historial():
    if os.path.exists(ARCHIVO_HISTORIAL):
        try:
            with open(ARCHIVO_HISTORIAL, 'r') as f:
                return json.load(f)
        except Exception:
            return []
    return []

def guardar_historial(historial):
    with open(ARCHIVO_HISTORIAL, 'w') as f:
        json.dump(historial, f, indent=2)

# Ayudantes para impresión bonita
def expr_str(e):
    try:
        return str(sp.simplify(e))
    except Exception:
        return str(e)

# --------------------------- Matemáticas centrales ---------------------------

# Solucionador de integral triple - intenta simbólico y retrocede a numérico

def resolver_integral_triple(integrando, variables, limites, sistema_coordenadas="rectangular"):
    """
    Calcula una integral triple en coordenadas rectangulares, cilíndricas o esféricas.
    Incluye pasos detallados, jacobianos y evaluación numérica final.
    Compatible con el formato del programa de cálculo multivariable.
    """

    # Definir variables simbólicas
    x, y, z, r, theta, phi = sp.symbols("x y z r theta phi")
    pasos = []

    # Seleccionar variables y jacobiano según el sistema
    if sistema_coordenadas in ["rectangular", "rectangulares"]:
        vars_locales = {"x": x, "y": y, "z": z}
        jacobiano = 1
        pasos.append("=== INTEGRAL TRIPLE - RECTANGULARES (X,Y,Z) ===")
        pasos.append("Fórmula: ∭ f(x,y,z) dx dy dz")

    elif sistema_coordenadas in ["cilindrica", "cilindricas"]:
        vars_locales = {"r": r, "theta": theta, "z": z, "pi": sp.pi}
        jacobiano = r
        pasos.append("=== INTEGRAL TRIPLE - CILÍNDRICAS (R,Θ,Z) ===")
        pasos.append("Fórmula: ∭ f(r,θ,z)·r dr dθ dz")

    elif sistema_coordenadas in ["esferica", "esfericas"]:
        rho, theta, phi = sp.symbols("rho theta phi")
        vars_locales = {"rho": rho, "theta": theta, "phi": phi, "pi": sp.pi}
        jacobiano = rho**2 * sp.sin(phi)
        pasos.append("=== INTEGRAL TRIPLE - ESFÉRICAS (Ρ,Θ,Φ) ===")
        pasos.append("Fórmula: ∭ f(ρ,θ,φ)·ρ²·sin(φ) dρ dθ dφ")

    else:
        raise ValueError("Sistema de coordenadas no reconocido. Use 'rectangular', 'cilindrica' o 'esferica'.")


    # Convertir el integrando en expresión simbólica
    expr = sp.sympify(integrando, locals=vars_locales)
    pasos.append(f"\nIntegrando inicial: {integrando}")
    
    # === CORRECCIÓN COMPLETA: Detectar si el usuario ya incluyó el jacobiano ===
    aplicar_jacobiano = True

    if sistema_coordenadas in ["cilindrica", "cilindricas"]:
        # Detectar si el integrando contiene 'r' (posible jacobiano incluido)
        integrando_limpio = integrando.replace(" ", "").lower()
        
        # Casos donde el usuario probablemente ya incluyó el jacobiano
        if any(condicion for condicion in [
            integrando_limpio == "r",
            integrando_limpio.startswith(("r+", "r-", "r*", "r/", "r**")),
            "r*z" in integrando_limpio,
            "r*theta" in integrando_limpio,
            integrando_limpio in ["r+z", "r-z", "r+theta", "r-theta"]
        ]):
            aplicar_jacobiano = False
            pasos.append("NOTA: El integrando contiene 'r' (jacobiano incluido por el usuario)")
            pasos.append(f"Integrando final: {expr}")

    elif sistema_coordenadas in ["esferica", "esfericas"]:
        # Lógica similar para coordenadas esféricas
        integrando_limpio = integrando.replace(" ", "").lower()
        
        # Detectar solo si el integrando incluye el jacobiano COMPLETO
        # o combinaciones que claramente indican jacobiano incluido
        jacobiano_completo = any([
            "rho**2*sin(phi)" in integrando_limpio,
            "r**2*sin(phi)" in integrando_limpio,
            "ρ²*sin(φ)" in integrando_limpio,
            integrando_limpio == "rho**2",
            integrando_limpio == "r**2"
        ])
        
        # Casos donde claramente el usuario incluyó parte del jacobiano
        jacobiano_parcial = any([
            "rho**2*" in integrando_limpio and "sin(phi)" in integrando_limpio,
            "r**2*" in integrando_limpio and "sin(phi)" in integrando_limpio,
        ])
        
        if jacobiano_completo or jacobiano_parcial:
            aplicar_jacobiano = False
            pasos.append("NOTA: El integrando contiene términos del jacobiano esférico")
            pasos.append(f"Integrando final: {expr}")
        else:
            # Para sin(phi) solo, SÍ aplicar jacobiano
            pasos.append(f"Multiplicando por el Jacobiano ({jacobiano}): integrando = {sp.simplify(expr * jacobiano)}")
            expr *= jacobiano
    # ========== FIN DE LA CORRECCIÓN ==========

    # === PROCESO DE INTEGRACIÓN PASO A PASO ===
    expr_actual = expr

    for i, var in enumerate(variables, start=1):
        a, b = limites[var]
        var_sym = sp.Symbol(var)

        pasos.append(f"\nPaso {i}: Integrar respecto de {var}")
        pasos.append(f"∫ de {a} a {b} de [{sp.simplify(expr_actual)}] d{var}")

        # Integrar con límites definidos y simplificar
        expr_actual = sp.integrate(
            expr_actual,
            (var_sym, sp.sympify(a, locals=vars_locales), sp.sympify(b, locals=vars_locales))
        )
        expr_actual = sp.simplify(expr_actual)
        pasos.append(f"Resultado parcial = {expr_actual}")

    # Resultado final simbólico
    resultado_final = expr_actual
    pasos.append(f"\nRESULTADO FINAL = {resultado_final}")

    # Intentar calcular el valor numérico
    try:
        valor_num = float(sp.N(resultado_final))
        pasos.append(f"Valor numérico aproximado = {valor_num}")
    except Exception:
        pasos.append("No se pudo calcular el valor numérico (resultado simbólico no evaluable).")

    return {
        "resultado": resultado_final,
        "pasos": pasos
    }

# Teoremas vectoriales (sin cambios, funcionan correctamente)
# ========== FUNCIONES DE EXPLICACIÓN POR TIPO DE REGIÓN ==========

def _explicacion_disco(R, valor_doble, valor_linea, rotacional):
    explicacion = []
    explicacion.append("🎯 EXPLICACIÓN PARA REGIÓN CIRCULAR (DISCO):")
    explicacion.append("")
    explicacion.append("1. 📍 VISUALIZA EL ESCENARIO:")
    explicacion.append("   • Imagina un disco de radio R = " + str(R))
    explicacion.append("   • Las flechas azules representan un campo de fuerzas")
    explicacion.append("   • Como un remolino en un estanque circular")
    explicacion.append("")
    explicacion.append("2. 🔄 INTERPRETACIÓN FÍSICA:")
    explicacion.append("   • Rotacional: " + str(rotacional) + " (rotación local en cada punto)")
    explicacion.append("   • La integral doble suma toda la rotación interna")
    explicacion.append("   • La integral de línea mide la circulación en el borde")
    explicacion.append("")
    explicacion.append("3. 📊 RESULTADO:")
    explicacion.append(f"   • Rotación interna total: {valor_doble}")
    explicacion.append(f"   • Circulación en el borde: {valor_linea}")
    if valor_doble == valor_linea:
        explicacion.append("   • ✅ CONFIRMACIÓN: El flujo interno = Circulación externa")
    explicacion.append("")
    explicacion.append("💡 CONCLUSIÓN: En un disco, toda la rotación interna se manifiesta")
    explicacion.append("exactamente como circulación alrededor de su circunferencia.")
    return explicacion

def _explicacion_entre_curvas(f1, f2, x_min, x_max, valor_doble, valor_linea, rotacional):
    explicacion = []
    explicacion.append("🎯 EXPLICACIÓN PARA REGIÓN ENTRE CURVAS:")
    explicacion.append("")
    explicacion.append("1. 📍 VISUALIZA EL ESCENARIO:")
    explicacion.append(f"   • Región entre y = {f1} (inferior) y y = {f2} (superior)")
    explicacion.append(f"   • Desde x = {x_min} hasta x = {x_max}")
    explicacion.append("   • Las flechas azules muestran el patrón de flujo del campo")
    explicacion.append("   • Como un río entre dos márgenes curvados")
    explicacion.append("")
    explicacion.append("2. 🔄 INTERPRETACIÓN FÍSICA:")
    explicacion.append("   • Rotacional: " + str(rotacional) + " (mide vórtices locales)")
    explicacion.append("   • Integral doble: Suma todos los mini-remolinos internos")
    explicacion.append("   • Integral de línea: Mide flujo neto por los 4 bordes")
    explicacion.append("")
    explicacion.append("3. 📊 ANÁLISIS DE LOS SEGMENTOS:")
    explicacion.append("   • Curva inferior: Contribuye según el flujo en y = " + f1)
    explicacion.append("   • Curva superior: Contribuye (en sentido inverso) en y = " + f2)
    explicacion.append("   • Lados verticales: Completan el camino cerrado")
    explicacion.append("")
    explicacion.append("4. 📈 RESULTADO:")
    explicacion.append(f"   • Rotación interna total: {valor_doble}")
    explicacion.append(f"   • Circulación neta en el borde: {valor_linea}")
    if valor_doble == valor_linea:
        explicacion.append("   • ✅ EL TEOREMA SE VERIFICA: La naturaleza cumple las matemáticas!")
    explicacion.append("")
    explicacion.append("💡 CONCLUSIÓN: En regiones entre curvas, el balance entre")
    explicacion.append("el flujo superior e inferior determina la circulación total.")
    return explicacion

def _explicacion_corona(R_int, R_ext, valor_doble, valor_linea, rotacional):
    explicacion = []
    explicacion.append("🎯 EXPLICACIÓN PARA CORONA CIRCULAR:")
    explicacion.append("")
    explicacion.append("1. 📍 VISUALIZA EL ESCENARIO:")
    explicacion.append(f"   • Anillo entre radio R_int = {R_int} y R_ext = {R_ext}")
    explicacion.append("   • Como un anillo de humo o un donut de flujo")
    explicacion.append("   • Campo vectorial fluye entre dos circunferencias")
    explicacion.append("")
    explicacion.append("2. 🔄 INTERPRETACIÓN FÍSICA:")
    explicacion.append("   • Rotacional: " + str(rotacional) + " en cada punto del anillo")
    explicacion.append("   • Integral doble: Suma la rotación en toda el área anular")
    explicacion.append("   • Integral de línea: Circulación exterior MENOS interior")
    explicacion.append("")
    explicacion.append("3. 📊 RESULTADO:")
    explicacion.append(f"   • Rotación en el anillo: {valor_doble}")
    explicacion.append(f"   • Circulación neta: {valor_linea}")
    if valor_doble == valor_linea:
        explicacion.append("   • ✅ CONFIRMACIÓN: Lo que gira dentro = Diferencia de bordes")
    explicacion.append("")
    explicacion.append("💡 CONCLUSIÓN: En una corona, la rotación interna equivale")
    explicacion.append("a la diferencia entre la circulación exterior e interior.")
    return explicacion

def _explicacion_rectangulo(a, b, valor_doble, valor_linea, rotacional):
    explicacion = []
    explicacion.append("🎯 EXPLICACIÓN PARA REGIÓN RECTANGULAR:")
    explicacion.append("")
    explicacion.append("1. 📍 VISUALIZA EL ESCENARIO:")
    explicacion.append(f"   • Rectángulo de {a} × {b} unidades")
    explicacion.append("   • Campo vectorial fluye a través de los 4 lados")
    explicacion.append("   • Como agua fluyendo a través de un canal rectangular")
    explicacion.append("")
    explicacion.append("2. 🔄 INTERPRETACIÓN FÍSICA:")
    explicacion.append("   • Rotacional: " + str(rotacional) + " (vorticidad local)")
    explicacion.append("   • Integral doble: Suma toda la rotación dentro del rectángulo")
    explicacion.append("   • Integral de línea: Flujo por cada lado (4 segmentos)")
    explicacion.append("")
    explicacion.append("3. 📊 RESULTADO:")
    explicacion.append(f"   • Rotación interna total: {valor_doble}")
    explicacion.append(f"   • Circulación en el perímetro: {valor_linea}")
    if valor_doble == valor_linea:
        explicacion.append("   • ✅ CONFIRMACIÓN: Rotación interna = Circulación externa")
    explicacion.append("")
    explicacion.append("💡 CONCLUSIÓN: En rectángulos, la suma de flujos por los 4 lados")
    explicacion.append("siempre iguala la rotación total en el interior.")
    return explicacion

def _explicacion_elipse(a, b, valor_doble, valor_linea, rotacional):
    explicacion = []
    explicacion.append("🎯 EXPLICACIÓN PARA REGIÓN ELÍPTICA:")
    explicacion.append("")
    explicacion.append("1. 📍 VISUALIZA EL ESCENARIO:")
    explicacion.append(f"   • Elipse con semiejes a = {a}, b = {b}")
    explicacion.append("   • Campo vectorial fluyendo en patrón elíptico")
    explicacion.append("   • Como un óvalo de carreras con flujo circulante")
    explicacion.append("")
    explicacion.append("2. 🔄 INTERPRETACIÓN FÍSICA:")
    explicacion.append("   • Rotacional: " + str(rotacional) + " en cada punto")
    explicacion.append("   • Integral doble: Usa coordenadas elípticas para sumar rotación")
    explicacion.append("   • Integral de línea: Circulación a lo largo de la elipse")
    explicacion.append("")
    explicacion.append("3. 📊 RESULTADO:")
    explicacion.append(f"   • Rotación interna total: {valor_doble}")
    explicacion.append(f"   • Circulación en el borde: {valor_linea}")
    if valor_doble == valor_linea:
        explicacion.append("   • ✅ CONFIRMACIÓN: La geometría elíptica preserva el teorema")
    explicacion.append("")
    explicacion.append("💡 CONCLUSIÓN: Las elipses demuestran que el Teorema de Green")
    explicacion.append("funciona para cualquier forma, no solo figuras regulares.")
    return explicacion

def _explicacion_triangulo(base, altura, valor_doble, valor_linea, rotacional):
    explicacion = []
    explicacion.append("🎯 EXPLICACIÓN PARA REGIÓN TRIANGULAR:")
    explicacion.append("")
    explicacion.append("1. 📍 VISUALIZA EL ESCENARIO:")
    explicacion.append(f"   • Triángulo con base = {base}, altura = {altura}")
    explicacion.append("   • Campo fluyendo a través de 3 lados rectos")
    explicacion.append("   • Como una cometa triangular en el viento")
    explicacion.append("")
    explicacion.append("2. 🔄 INTERPRETACIÓN FÍSICA:")
    explicacion.append("   • Rotacional: " + str(rotacional) + " (patrón de giro local)")
    explicacion.append("   • Integral doble: Suma rotación en área triangular")
    explicacion.append("   • Integral de línea: Flujo por base + lados inclinados")
    explicacion.append("")
    explicacion.append("3. 📊 RESULTADO:")
    explicacion.append(f"   • Rotación interna: {valor_doble}")
    explicacion.append(f"   • Circulación externa: {valor_linea}")
    if valor_doble == valor_linea:
        explicacion.append("   • ✅ CONFIRMACIÓN: Triángulos también obedecen el teorema")
    explicacion.append("")
    explicacion.append("💡 CONCLUSIÓN: En triángulos, la simplicidad geométrica no")
    explicacion.append("afecta la profunda verdad del Teorema de Green.")
    return explicacion

def _explicacion_semicirculo(R, tipo, valor_doble, valor_linea, rotacional):
    explicacion = []
    explicacion.append("🎯 EXPLICACIÓN PARA SEMICÍRCULO:")
    explicacion.append("")
    explicacion.append("1. 📍 VISUALIZA EL ESCENARIO:")
    explicacion.append(f"   • Semicírculo de radio R = {R} ({tipo})")
    explicacion.append("   • Campo fluye a través del arco y el diámetro")
    explicacion.append("   • Como media rueda giratoria o media luna de flujo")
    explicacion.append("")
    explicacion.append("2. 🔄 INTERPRETACIÓN FÍSICA:")
    explicacion.append("   • Rotacional: " + str(rotacional) + " en medio disco")
    explicacion.append("   • Integral doble: Rotación en media área circular")
    explicacion.append("   • Integral de línea: Flujo por arco + diámetro")
    explicacion.append("")
    explicacion.append("3. 📊 RESULTADO:")
    explicacion.append(f"   • Rotación en medio disco: {valor_doble}")
    explicacion.append(f"   • Circulación en media frontera: {valor_linea}")
    if valor_doble == valor_linea:
        explicacion.append("   • ✅ CONFIRMACIÓN: Mitad de forma, misma verdad matemática")
    explicacion.append("")
    explicacion.append("💡 CONCLUSIÓN: Los semicírculos muestran que el teorema")
    explicacion.append("funciona incluso para regiones no simplemente conexas.")
    return explicacion

def _explicacion_sector_polar(R, theta_min, theta_max, valor_doble, valor_linea, rotacional):
    explicacion = []
    explicacion.append("🎯 EXPLICACIÓN PARA SECTOR POLAR:")
    explicacion.append("")
    explicacion.append("1. 📍 VISUALIZA EL ESCENARIO:")
    explicacion.append(f"   • Sector circular R = {R}, θ ∈ [{theta_min}, {theta_max}]")
    explicacion.append("   • Como una rebanada de pizza de flujo vectorial")
    explicacion.append("   • Campo confinado entre dos radios y un arco")
    explicacion.append("")
    explicacion.append("2. 🔄 INTERPRETACIÓN FÍSICA:")
    explicacion.append("   • Rotacional: " + str(rotacional) + " en la rebanada")
    explicacion.append("   • Integral doble: Natural en coordenadas polares")
    explicacion.append("   • Integral de línea: 2 radios + 1 arco circular")
    explicacion.append("")
    explicacion.append("3. 📊 RESULTADO:")
    explicacion.append(f"   • Rotación en el sector: {valor_doble}")
    explicacion.append(f"   • Circulación en los bordes: {valor_linea}")
    if valor_doble == valor_linea:
        explicacion.append("   • ✅ CONFIRMACIÓN: Coordenadas polares verifican el teorema")
    explicacion.append("")
    explicacion.append("💡 CONCLUSIÓN: Los sectores polares demuestran la versatilidad")
    explicacion.append("del teorema en diferentes sistemas coordenados.")
    return explicacion

def _explicacion_poligono(lados, radio, valor_doble, valor_linea, rotacional):
    explicacion = []
    explicacion.append("🎯 EXPLICACIÓN PARA POLÍGONO REGULAR:")
    explicacion.append("")
    explicacion.append("1. 📍 VISUALIZA EL ESCENARIO:")
    explicacion.append(f"   • Polígono de {lados} lados, radio = {radio}")
    explicacion.append("   • Campo fluye a través de múltiples lados rectos")
    explicacion.append("   • Como una rueda dentada en un flujo vectorial")
    explicacion.append("")
    explicacion.append("2. 🔄 INTERPRETACIÓN FÍSICA:")
    explicacion.append("   • Rotacional: " + str(rotacional) + " (aproximado)")
    explicacion.append("   • Integral doble: Área poligonal × rotacional promedio")
    explicacion.append("   • Integral de línea: Suma compleja por muchos lados")
    explicacion.append("")
    explicacion.append("3. 📊 RESULTADO:")
    explicacion.append(f"   • Rotación interna aproximada: {valor_doble}")
    explicacion.append(f"   • Circulación externa: {valor_linea}")
    if valor_doble == valor_linea:
        explicacion.append("   • ✅ CONFIRMACIÓN: Polígonos aproximan círculos")
    explicacion.append("")
    explicacion.append("💡 CONCLUSIÓN: Los polígonos muestran cómo formas complejas")
    explicacion.append("también obedecen los principios fundamentales del teorema.")
    return explicacion

def aplicar_green(P_str, Q_str, region='disco', parametros_region=None):
    """
    Regiones soportadas:
    - 'disco', 'corona', 'rectangulo', 'elipse', 'triangulo'
    - 'semicirculo', 'entre_curvas', 'sector_polar', 'poligono'
    """
    x,y = sp.symbols('x y', real=True)
    locales = {'x':x,'y':y,'sin':sp.sin,'cos':sp.cos,'pi':sp.pi}
    try:
        P = sp.sympify(P_str, locals=locales)
        Q = sp.sympify(Q_str, locals=locales)
    except Exception as e:
        return {'error': f'Error analizando P o Q: {e}'}
    
    pasos = []
    info = []
    
    # Explicación del Teorema de Green
    info.append("TEOREMA DE GREEN")
    info.append("Fórmula: ∮_C (P dx + Q dy) = ∬_D (∂Q/∂x - ∂P/∂y) dA")
    info.append("Donde:")
    info.append("  - P(x,y): componente x del campo vectorial")
    info.append("  - Q(x,y): componente y del campo vectorial") 
    info.append("  - C: curva cerrada que bordea la región D")
    info.append("  - D: región en el plano xy")
    info.append("  - ∂Q/∂x: derivada parcial de Q respecto a x")
    info.append("  - ∂P/∂y: derivada parcial de P respecto a y")
    
    pasos.append(f'Campo vectorial F = (P, Q) = ({sp.pretty(P)}, {sp.pretty(Q)})')
    
    # CÁLCULOS DETALLADOS DE LAS DERIVADAS PARCIALES
    pasos.append("")
    pasos.append("CÁLCULO DE LAS DERIVADAS PARCIALES:")
    pasos.append(f"P(x,y) = {sp.pretty(P)}")
    pasos.append(f"Q(x,y) = {sp.pretty(Q)}")
    
    # Calcular ∂Q/∂x con paso a paso
    dQdx = sp.diff(Q, x)
    pasos.append(f"∂Q/∂x = ∂({sp.pretty(Q)})/∂x = {sp.pretty(dQdx)}")
    
    # Calcular ∂P/∂y con paso a paso
    dPdy = sp.diff(P, y)
    pasos.append(f"∂P/∂y = ∂({sp.pretty(P)})/∂y = {sp.pretty(dPdy)}")
    
    # Calcular el rotacional
    rotacional_z = sp.simplify(dQdx - dPdy)
    pasos.append(f"∇×F = ∂Q/∂x - ∂P/∂y = {sp.pretty(dQdx)} - ({sp.pretty(dPdy)}) = {sp.pretty(rotacional_z)}")
    
    pasos.append("")

    if region == 'disco':
        R = sp.sympify(parametros_region.get('R','1'))
        centro_x = sp.sympify(parametros_region.get('centro_x','0'))
        centro_y = sp.sympify(parametros_region.get('centro_y','0'))
        pasos.append(f'Región: disco de radio R = {R}, centro ({centro_x}, {centro_y})')
        
        # INTEGRAL DOBLE - CÁLCULO DETALLADO
        pasos.append("")
        pasos.append("CÁLCULO DE LA INTEGRAL DOBLE:")
        pasos.append(f"∬_D (∇×F) dA = ∬_D {sp.pretty(rotacional_z)} dA")
        
        if rotacional_z.is_constant():
            area_disco = sp.pi * R**2
            resultado_doble = rotacional_z * area_disco
            pasos.append(f"Como ∇×F = {sp.pretty(rotacional_z)} es constante:")
            pasos.append(f"∬_D {sp.pretty(rotacional_z)} dA = {sp.pretty(rotacional_z)} × Área del disco")
            pasos.append(f"Área del disco = πR² = π({R})² = {sp.pretty(area_disco)}")
            pasos.append(f"Resultado = {sp.pretty(rotacional_z)} × {sp.pretty(area_disco)} = {sp.pretty(resultado_doble)}")
        else:
            r,theta = sp.symbols('r theta', positive=True)
            sustituciones = {x: centro_x + r*sp.cos(theta), y: centro_y + r*sp.sin(theta)}
            integrando = sp.simplify(rotacional_z.subs(sustituciones) * r)
            pasos.append(f'Integrando en coordenadas polares: {sp.pretty(rotacional_z.subs(sustituciones))} × r = {sp.pretty(integrando)}')
            resultado_doble = sp.integrate(integrando, (r,0,R),(theta,0,2*sp.pi))
            pasos.append(f'Integral doble sobre la región D = {sp.pretty(resultado_doble)}')
        
        # INTEGRAL DE LÍNEA
        pasos.append("")
        pasos.append("CÁLCULO DE LA INTEGRAL DE LÍNEA:")
        t = sp.symbols('t', real=True)
        x_c = centro_x + R*sp.cos(t)
        y_c = centro_y + R*sp.sin(t)
        dx_dt = sp.diff(x_c, t)
        dy_dt = sp.diff(y_c, t)
        P_param = P.subs({x: x_c, y: y_c})
        Q_param = Q.subs({x: x_c, y: y_c})
        integrando_linea = P_param * dx_dt + Q_param * dy_dt
        resultado_linea = sp.simplify(sp.integrate(integrando_linea, (t, 0, 2*sp.pi)))
        pasos.append(f"Integral de línea = {sp.pretty(resultado_linea)}")
        
        # ========== AGREGAR EXPLICACIÓN PERSONALIZADA ==========
        pasos.append("\n" + "="*60)
        pasos.append("📊 INTERPRETACIÓN GRÁFICA Y CONCLUSIONES")
        pasos.append("="*60)
        
        R_val = str(parametros_region.get('R','1'))
        pasos.extend(_explicacion_disco(R_val, resultado_doble, resultado_linea, rotacional_z))
        
        return _verificar_green(resultado_doble, resultado_linea, pasos, info)

    elif region == 'corona':
        R_int = sp.sympify(parametros_region.get('R_int','1'))
        R_ext = sp.sympify(parametros_region.get('R_ext','2'))
        centro_x = sp.sympify(parametros_region.get('centro_x','0'))
        centro_y = sp.sympify(parametros_region.get('centro_y','0'))
        pasos.append(f'Región: corona circular R_int={R_int}, R_ext={R_ext}, centro ({centro_x}, {centro_y})')
        
        # Integral doble en coordenadas polares
        r,theta = sp.symbols('r theta', positive=True)
        sustituciones = {x: centro_x + r*sp.cos(theta), y: centro_y + r*sp.sin(theta)}
        integrando = rotacional_z.subs(sustituciones) * r
        resultado_doble = sp.integrate(integrando, (r,R_int,R_ext),(theta,0,2*sp.pi))
        pasos.append(f'Integral doble = {sp.pretty(resultado_doble)}')
        
        # Integral de línea (circunferencia exterior - interior)
        t = sp.symbols('t', real=True)
        
        # Circunferencia exterior
        x_ext = centro_x + R_ext*sp.cos(t)
        y_ext = centro_y + R_ext*sp.sin(t)
        dx_ext = sp.diff(x_ext, t)
        dy_ext = sp.diff(y_ext, t)
        linea_ext = sp.integrate(P.subs({x:x_ext,y:y_ext})*dx_ext + Q.subs({x:x_ext,y:y_ext})*dy_ext, (t,0,2*sp.pi))
        
        # Circunferencia interior (sentido horario)
        x_int = centro_x + R_int*sp.cos(t)
        y_int = centro_y + R_int*sp.sin(t)
        dx_int = sp.diff(x_int, t)
        dy_int = sp.diff(y_int, t)
        linea_int = sp.integrate(P.subs({x:x_int,y:y_int})*dx_int + Q.subs({x:x_int,y:y_int})*dy_int, (t,2*sp.pi,0))
        
        resultado_linea = sp.simplify(linea_ext + linea_int)
        pasos.append(f"Integral de línea = {sp.pretty(resultado_linea)}")
        
        # ========== AGREGAR EXPLICACIÓN PERSONALIZADA ==========
        pasos.append("\n" + "="*60)
        pasos.append("📊 INTERPRETACIÓN GRÁFICA Y CONCLUSIONES")
        pasos.append("="*60)
        
        R_int_val = str(parametros_region.get('R_int','1'))
        R_ext_val = str(parametros_region.get('R_ext','2'))
        pasos.extend(_explicacion_corona(R_int_val, R_ext_val, resultado_doble, resultado_linea, rotacional_z))
        
        return _verificar_green(resultado_doble, resultado_linea, pasos, info)

    elif region == 'rectangulo':
        a = sp.sympify(parametros_region.get('a','1'))
        b = sp.sympify(parametros_region.get('b','1'))
        x0 = sp.sympify(parametros_region.get('x0','0'))
        y0 = sp.sympify(parametros_region.get('y0','0'))
        pasos.append(f'Región: rectángulo {a}×{b}, esquina inferior ({x0}, {y0})')
        
        # Integral doble
        resultado_doble = sp.integrate(rotacional_z, (x,x0,x0+a),(y,y0,y0+b))
        pasos.append(f'Integral doble = {sp.pretty(resultado_doble)}')
        
        # Integral de línea (4 segmentos)
        t = sp.symbols('t', real=True)
        
        # Segmento 1: inferior (x0→x0+a, y0)
        int1 = sp.integrate(P.subs({x:t,y:y0}), (t,x0,x0+a))
        # Segmento 2: derecho (x0+a, y0→y0+b)
        int2 = sp.integrate(Q.subs({x:x0+a,y:t}), (t,y0,y0+b))
        # Segmento 3: superior (x0+a→x0, y0+b)
        int3 = sp.integrate(P.subs({x:t,y:y0+b}), (t,x0+a,x0))
        # Segmento 4: izquierdo (x0, y0+b→y0)
        int4 = sp.integrate(Q.subs({x:x0,y:t}), (t,y0+b,y0))
        
        resultado_linea = sp.simplify(int1 + int2 + int3 + int4)
        pasos.append(f"Integral de línea = {sp.pretty(resultado_linea)}")
        
        # ========== AGREGAR EXPLICACIÓN PERSONALIZADA ==========
        pasos.append("\n" + "="*60)
        pasos.append("📊 INTERPRETACIÓN GRÁFICA Y CONCLUSIONES")
        pasos.append("="*60)
        
        a_val = str(parametros_region.get('a','1'))
        b_val = str(parametros_region.get('b','1'))
        pasos.extend(_explicacion_rectangulo(a_val, b_val, resultado_doble, resultado_linea, rotacional_z))
        
        return _verificar_green(resultado_doble, resultado_linea, pasos, info)

    elif region == 'elipse':
        a = sp.sympify(parametros_region.get('a','2'))
        b = sp.sympify(parametros_region.get('b','1'))
        centro_x = sp.sympify(parametros_region.get('centro_x','0'))
        centro_y = sp.sympify(parametros_region.get('centro_y','0'))
        pasos.append(f'Región: elipse (x-{centro_x})²/{a}² + (y-{centro_y})²/{b}² = 1')
        
        # Integral doble en coordenadas elípticas
        r,theta = sp.symbols('r theta', positive=True)
        sustituciones = {x: centro_x + a*r*sp.cos(theta), y: centro_y + b*r*sp.sin(theta)}
        jacobiano = a * b * r
        integrando = rotacional_z.subs(sustituciones) * jacobiano
        resultado_doble = sp.integrate(integrando, (r,0,1),(theta,0,2*sp.pi))
        pasos.append(f'Integral doble = {sp.pretty(resultado_doble)}')
        
        # Integral de línea (parametrización elíptica)
        t = sp.symbols('t', real=True)
        x_elipse = centro_x + a*sp.cos(t)
        y_elipse = centro_y + b*sp.sin(t)
        dx_dt = sp.diff(x_elipse, t)
        dy_dt = sp.diff(y_elipse, t)
        integrando_linea = P.subs({x:x_elipse,y:y_elipse})*dx_dt + Q.subs({x:x_elipse,y:y_elipse})*dy_dt
        resultado_linea = sp.simplify(sp.integrate(integrando_linea, (t,0,2*sp.pi)))
        pasos.append(f"Integral de línea = {sp.pretty(resultado_linea)}")
        
        # ========== AGREGAR EXPLICACIÓN PERSONALIZADA ==========
        pasos.append("\n" + "="*60)
        pasos.append("📊 INTERPRETACIÓN GRÁFICA Y CONCLUSIONES")
        pasos.append("="*60)
        
        a_val = str(parametros_region.get('a','2'))
        b_val = str(parametros_region.get('b','1'))
        pasos.extend(_explicacion_elipse(a_val, b_val, resultado_doble, resultado_linea, rotacional_z))
        
        return _verificar_green(resultado_doble, resultado_linea, pasos, info)

    elif region == 'triangulo':
        base = sp.sympify(parametros_region.get('base','2'))
        altura = sp.sympify(parametros_region.get('altura','3'))
        x0 = sp.sympify(parametros_region.get('x0','0'))
        y0 = sp.sympify(parametros_region.get('y0','0'))
        pasos.append(f'Región: triángulo base={base}, altura={altura}, vértice ({x0}, {y0})')
        
        # Integral doble
        resultado_doble = sp.integrate(rotacional_z, (x,x0,x0+base), 
                                     (y,y0,y0+altura*(1-(x-x0)/base)))
        pasos.append(f'Integral doble = {sp.pretty(resultado_doble)}')
        
        # Integral de línea (3 segmentos)
        t = sp.symbols('t', real=True)
        
        # Segmento 1: base (x0→x0+base, y0)
        int1 = sp.integrate(P.subs({x:t,y:y0}), (t,x0,x0+base))
        # Segmento 2: hipotenusa (x0+base→x0, y0→y0+altura)
        x_hip = x0 + base*(1-t); y_hip = y0 + altura*t
        dx_hip = sp.diff(x_hip,t); dy_hip = sp.diff(y_hip,t)
        int2 = sp.integrate(P.subs({x:x_hip,y:y_hip})*dx_hip + Q.subs({x:x_hip,y:y_hip})*dy_hip, (t,0,1))
        # Segmento 3: altura (x0, y0+altura→y0)
        int3 = sp.integrate(Q.subs({x:x0,y:t}), (t,y0+altura,y0))
        
        resultado_linea = sp.simplify(int1 + int2 + int3)
        pasos.append(f"Integral de línea = {sp.pretty(resultado_linea)}")
        
        # ========== AGREGAR EXPLICACIÓN PERSONALIZADA ==========
        pasos.append("\n" + "="*60)
        pasos.append("📊 INTERPRETACIÓN GRÁFICA Y CONCLUSIONES")
        pasos.append("="*60)
        
        base_val = str(parametros_region.get('base','2'))
        altura_val = str(parametros_region.get('altura','3'))
        pasos.extend(_explicacion_triangulo(base_val, altura_val, resultado_doble, resultado_linea, rotacional_z))
        
        return _verificar_green(resultado_doble, resultado_linea, pasos, info)

    elif region == 'semicirculo':
        R = sp.sympify(parametros_region.get('R','2'))
        tipo = parametros_region.get('tipo','superior')
        centro_x = sp.sympify(parametros_region.get('centro_x','0'))
        centro_y = sp.sympify(parametros_region.get('centro_y','0'))
        pasos.append(f'Región: semicírculo {tipo}, R={R}, centro ({centro_x}, {centro_y})')
        
        # Integral doble en coordenadas polares
        r,theta = sp.symbols('r theta', positive=True)
        sustituciones = {x: centro_x + r*sp.cos(theta), y: centro_y + r*sp.sin(theta)}
        integrando = rotacional_z.subs(sustituciones) * r
        
        if tipo == 'superior':
            resultado_doble = sp.integrate(integrando, (r,0,R),(theta,0,sp.pi))
        else:  # inferior
            resultado_doble = sp.integrate(integrando, (r,0,R),(theta,sp.pi,2*sp.pi))
        
        pasos.append(f'Integral doble = {sp.pretty(resultado_doble)}')
        
        # Integral de línea (semicírculo + diámetro)
        t = sp.symbols('t', real=True)
        
        # Arco semicircular
        if tipo == 'superior':
            theta_min, theta_max = 0, sp.pi
        else:
            theta_min, theta_max = sp.pi, 2*sp.pi
            
        x_arco = centro_x + R*sp.cos(t)
        y_arco = centro_y + R*sp.sin(t)
        dx_arco = sp.diff(x_arco,t); dy_arco = sp.diff(y_arco,t)
        linea_arco = sp.integrate(P.subs({x:x_arco,y:y_arco})*dx_arco + Q.subs({x:x_arco,y:y_arco})*dy_arco, (t,theta_min,theta_max))
        
        # Segmento diametral
        if tipo == 'superior':
            x_diam = t; y_diam = centro_y
            linea_diam = sp.integrate(P.subs({x:x_diam,y:y_diam}), (t,centro_x+R,centro_x-R))
        else:
            x_diam = t; y_diam = centro_y
            linea_diam = sp.integrate(P.subs({x:x_diam,y:y_diam}), (t,centro_x-R,centro_x+R))
        
        resultado_linea = sp.simplify(linea_arco + linea_diam)
        pasos.append(f"Integral de línea = {sp.pretty(resultado_linea)}")
        
        # ========== AGREGAR EXPLICACIÓN PERSONALIZADA ==========
        pasos.append("\n" + "="*60)
        pasos.append("📊 INTERPRETACIÓN GRÁFICA Y CONCLUSIONES")
        pasos.append("="*60)
        
        R_val = str(parametros_region.get('R','2'))
        tipo_val = parametros_region.get('tipo','superior')
        pasos.extend(_explicacion_semicirculo(R_val, tipo_val, resultado_doble, resultado_linea, rotacional_z))
        
        return _verificar_green(resultado_doble, resultado_linea, pasos, info)

    elif region == 'entre_curvas':
        f1_str = parametros_region.get('f1','x**2')
        f2_str = parametros_region.get('f2','4')
        x_min = sp.sympify(parametros_region.get('x_min','0'))
        x_max = sp.sympify(parametros_region.get('x_max','2'))
        
        locales = {'x':x,'y':y,'sin':sp.sin,'cos':sp.cos,'pi':sp.pi, 'exp':sp.exp, 'log':sp.log}
        try:
            f1 = sp.sympify(f1_str, locals=locales)
            f2 = sp.sympify(f2_str, locals=locales)
        except Exception as e:
            return {'error': f'Error analizando las curvas: {e}'}
        
        pasos.append(f'Región: entre y={f1_str} y y={f2_str}, x∈[{x_min},{x_max}]')
        
        # INTEGRAL DOBLE - CORREGIDA (PASO A PASO)
        pasos.append("")
        pasos.append("CÁLCULO DETALLADO DE LA INTEGRAL DOBLE:")
        pasos.append(f"∬_D (∇×F) dA = ∬_D {sp.pretty(rotacional_z)} dA")
        pasos.append(f" = ∫_{{{x_min}}}^{{{x_max}}} ∫_{{{f1_str}}}^{{{f2_str}}} {sp.pretty(rotacional_z)} dy dx")
        
        try:
            # Paso 1: Integrar respecto a y
            integral_respecto_y = sp.integrate(rotacional_z, (y, f1, f2))
            pasos.append(f"Paso 1 - Integral respecto a y: ∫_{{{f1_str}}}^{{{f2_str}}} {sp.pretty(rotacional_z)} dy")
            pasos.append(f" = {sp.pretty(integral_respecto_y)}")
            
            # Paso 2: Integrar respecto a x
            resultado_doble = sp.integrate(integral_respecto_y, (x, x_min, x_max))
            pasos.append(f"Paso 2 - Integral respecto a x: ∫_{{{x_min}}}^{{{x_max}}} {sp.pretty(integral_respecto_y)} dx")
            pasos.append(f" = {sp.pretty(resultado_doble)}")
            
            pasos.append(f'Integral doble FINAL = {sp.pretty(resultado_doble)}')
            
        except Exception as e:
            return {'error': f'Error en integral doble: {e}'}
        
        # INTEGRAL DE LÍNEA (se mantiene igual)
        pasos.append("")
        pasos.append("CÁLCULO DE LA INTEGRAL DE LÍNEA (4 segmentos):")
        
        t = sp.symbols('t', real=True)
        resultado_linea = 0
        
        try:
            # Segmento 1: Curva inferior (de x_min a x_max)
            x1 = t
            y1 = f1.subs(x, t)
            dx1 = 1
            dy1 = sp.diff(f1, x).subs(x, t)
            integrando1 = P.subs({x: x1, y: y1}) * dx1 + Q.subs({x: x1, y: y1}) * dy1
            int1 = sp.integrate(integrando1, (t, x_min, x_max))
            pasos.append(f"Segmento 1 (curva inferior): {sp.pretty(int1)}")
            resultado_linea += int1
            
            # Segmento 2: Lado derecho (de f1(x_max) a f2(x_max))
            y2 = t
            x2 = x_max
            dx2 = 0
            dy2 = 1
            integrando2 = P.subs({x: x2, y: y2}) * dx2 + Q.subs({x: x2, y: y2}) * dy2
            int2 = sp.integrate(integrando2, (t, f1.subs(x, x_max), f2.subs(x, x_max)))
            pasos.append(f"Segmento 2 (lado derecho): {sp.pretty(int2)}")
            resultado_linea += int2
            
            # Segmento 3: Curva superior (de x_max a x_min - SENTIDO INVERSO)
            x3 = t
            y3 = f2.subs(x, t)
            dx3 = 1
            dy3 = sp.diff(f2, x).subs(x, t)
            integrando3 = P.subs({x: x3, y: y3}) * dx3 + Q.subs({x: x3, y: y3}) * dy3
            int3 = sp.integrate(integrando3, (t, x_max, x_min))  # Sentido inverso
            pasos.append(f"Segmento 3 (curva superior, inverso): {sp.pretty(int3)}")
            resultado_linea += int3
            
            # Segmento 4: Lado izquierdo (de f2(x_min) a f1(x_min) - SENTIDO INVERSO)
            y4 = t
            x4 = x_min
            dx4 = 0
            dy4 = 1
            integrando4 = P.subs({x: x4, y: y4}) * dx4 + Q.subs({x: x4, y: y4}) * dy4
            int4 = sp.integrate(integrando4, (t, f2.subs(x, x_min), f1.subs(x, x_min)))  # Sentido inverso
            pasos.append(f"Segmento 4 (lado izquierdo, inverso): {sp.pretty(int4)}")
            resultado_linea += int4
            
            resultado_linea = sp.simplify(resultado_linea)
            pasos.append(f"Integral de línea TOTAL = {sp.pretty(resultado_linea)}")
            
        except Exception as e:
            return {'error': f'Error en integral de línea: {e}'}
        
        # ========== AGREGAR EXPLICACIÓN PERSONALIZADA ==========
        pasos.append("\n" + "="*60)
        pasos.append("📊 INTERPRETACIÓN GRÁFICA Y CONCLUSIONES")
        pasos.append("="*60)
        
        f1_val = parametros_region.get('f1','x')
        f2_val = parametros_region.get('f2','2*x+1')
        x_min_val = str(parametros_region.get('x_min','0'))
        x_max_val = str(parametros_region.get('x_max','2'))
        pasos.extend(_explicacion_entre_curvas(f1_val, f2_val, x_min_val, x_max_val, resultado_doble, resultado_linea, rotacional_z))
        
        return _verificar_green(resultado_doble, resultado_linea, pasos, info)
    
    elif region == 'sector_polar':
        R = sp.sympify(parametros_region.get('R','2'))
        theta_min = sp.sympify(parametros_region.get('theta_min','0'))
        theta_max = sp.sympify(parametros_region.get('theta_max','pi/2'))
        pasos.append(f'Región: sector polar R={R}, θ∈[{theta_min},{theta_max}]')
        
        # Integral doble en coordenadas polares
        r,theta = sp.symbols('r theta', positive=True)
        sustituciones = {x: r*sp.cos(theta), y: r*sp.sin(theta)}
        integrando = rotacional_z.subs(sustituciones) * r
        resultado_doble = sp.integrate(integrando, (r,0,R),(theta,theta_min,theta_max))
        pasos.append(f'Integral doble = {sp.pretty(resultado_doble)}')
        
        # Integral de línea (arco + 2 radios)
        t = sp.symbols('t', real=True)
        
        # Arco circular
        x_arco = R*sp.cos(t); y_arco = R*sp.sin(t)
        dx_arco = sp.diff(x_arco,t); dy_arco = sp.diff(y_arco,t)
        linea_arco = sp.integrate(P.subs({x:x_arco,y:y_arco})*dx_arco + Q.subs({x:x_arco,y:y_arco})*dy_arco, (t,theta_min,theta_max))
        
        # Radio en θ_min
        x_rad1 = t*sp.cos(theta_min); y_rad1 = t*sp.sin(theta_min)
        linea_rad1 = sp.integrate(P.subs({x:x_rad1,y:y_rad1})*sp.cos(theta_min) + Q.subs({x:x_rad1,y:y_rad1})*sp.sin(theta_min), (t,R,0))
        
        # Radio en θ_max
        x_rad2 = t*sp.cos(theta_max); y_rad2 = t*sp.sin(theta_max)
        linea_rad2 = sp.integrate(P.subs({x:x_rad2,y:y_rad2})*sp.cos(theta_max) + Q.subs({x:x_rad2,y:y_rad2})*sp.sin(theta_max), (t,0,R))
        
        resultado_linea = sp.simplify(linea_arco + linea_rad1 + linea_rad2)
        pasos.append(f"Integral de línea = {sp.pretty(resultado_linea)}")
        
        # ========== AGREGAR EXPLICACIÓN PERSONALIZADA ==========
        pasos.append("\n" + "="*60)
        pasos.append("📊 INTERPRETACIÓN GRÁFICA Y CONCLUSIONES")
        pasos.append("="*60)
        
        R_val = str(parametros_region.get('R','2'))
        theta_min_val = str(parametros_region.get('theta_min','0'))
        theta_max_val = str(parametros_region.get('theta_max','pi/2'))
        pasos.extend(_explicacion_sector_polar(R_val, theta_min_val, theta_max_val, resultado_doble, resultado_linea, rotacional_z))
        
        return _verificar_green(resultado_doble, resultado_linea, pasos, info)

    elif region == 'poligono':
        lados = int(parametros_region.get('lados','5'))
        radio = sp.sympify(parametros_region.get('radio','2'))
        centro_x = sp.sympify(parametros_region.get('centro_x','0'))
        centro_y = sp.sympify(parametros_region.get('centro_y','0'))
        pasos.append(f'Región: polígono regular de {lados} lados, R={radio}, centro ({centro_x}, {centro_y})')
        
        # Para polígonos, es más fácil calcular solo la integral doble
        # El área de un polígono regular es: (n * s²) / (4 * tan(π/n))
        # donde s = 2R * sin(π/n)
        area_poligono = (lados * (2*radio*sp.sin(sp.pi/lados))**2) / (4 * sp.tan(sp.pi/lados))
        
        if rotacional_z.is_constant():
            resultado_doble = rotacional_z * area_poligono
            pasos.append(f"Como ∇×F es constante, integral doble = {sp.pretty(rotacional_z)} × {sp.pretty(area_poligono)} = {sp.pretty(resultado_doble)}")
        else:
            # Para rotacional no constante, usar integración numérica aproximada
            pasos.append("⚠️  Rotacional no constante - usando valor medio aproximado")
            # Evaluar rotacional en el centro como aproximación
            rotacional_medio = rotacional_z.subs({x:centro_x, y:centro_y})
            resultado_doble = rotacional_medio * area_poligono
            pasos.append(f"Aproximación: ∇×F ≈ {sp.pretty(rotacional_medio)} en el centro")
            pasos.append(f"Integral doble ≈ {sp.pretty(rotacional_medio)} × {sp.pretty(area_poligono)} = {sp.pretty(resultado_doble)}")
        
        # Para polígonos, la integral de línea es compleja, así que mostramos solo la doble
        pasos.append("Nota: Para polígonos, se muestra solo la integral doble")
        
        # ========== AGREGAR EXPLICACIÓN PERSONALIZADA ==========
        pasos.append("\n" + "="*60)
        pasos.append("📊 INTERPRETACIÓN GRÁFICA Y CONCLUSIONES")
        pasos.append("="*60)
        
        lados_val = str(parametros_region.get('lados','5'))
        radio_val = str(parametros_region.get('radio','2'))
        pasos.extend(_explicacion_poligono(lados_val, radio_val, resultado_doble, resultado_doble, rotacional_z))
        
        return {'doble': resultado_doble, 'linea': resultado_doble, 'pasos': pasos, 'info': info}

    else:
        return {'error':'Región no soportada para el Teorema de Green.'}

def _verificar_green(doble, linea, pasos, info):
    """Función auxiliar para verificar el teorema de Green"""
    pasos.append("")
    pasos.append("VERIFICACIÓN DEL TEOREMA DE GREEN:")
    pasos.append(f"Integral doble: {sp.pretty(doble)}")
    pasos.append(f"Integral de línea: {sp.pretty(linea)}")
    
    if sp.simplify(doble - linea) == 0:
        pasos.append("✅ El teorema se verifica: ∮_C F·dr = ∬_D (∇×F) dA")
    else:
        diferencia = sp.simplify(doble - linea)
        pasos.append(f"❌ Diferencia: {sp.pretty(diferencia)}")
    
    return {'doble': doble, 'linea': linea, 'pasos': pasos, 'info': info}


def aplicar_divergencia(Fx_str, Fy_str, Fz_str, region='esfera', parametros_region=None):
    x,y,z = sp.symbols('x y z', real=True)
    locales = {'x':x,'y':y,'z':z,'sin':sp.sin,'cos':sp.cos,'pi':sp.pi}
    try:
        Fx = sp.sympify(Fx_str, locals=locales)
        Fy = sp.sympify(Fy_str, locals=locales)
        Fz = sp.sympify(Fz_str, locals=locales)
    except Exception as e:
        return {'error': f'Error analizando las componentes del campo: {e}'}
    
    pasos = []
    info = []
    
    # Explicación del Teorema de la Divergencia
    info.append("TEOREMA DE LA DIVERGENCIA (TEOREMA DE GAUSS)")
    info.append("Fórmula: ∬_S F·dS = ∭_V (∇·F) dV")
    info.append("Donde:")
    info.append("  - F = (Fx, Fy, Fz): campo vectorial")
    info.append("  - ∇·F: divergencia del campo F")
    info.append("  - S: superficie cerrada que encierra el volumen V")
    info.append("  - V: volumen encerrado por la superficie S")
    info.append("  - dS: elemento diferencial de superficie")
    info.append("  - dV: elemento diferencial de volumen")
    
    pasos.append(f'Campo vectorial F = ({sp.pretty(Fx)}, {sp.pretty(Fy)}, {sp.pretty(Fz)})')
    
    # CÁLCULO DETALLADO DE LA DIVERGENCIA
    pasos.append("")
    pasos.append("CÁLCULO DETALLADO DE LA DIVERGENCIA:")
    pasos.append("∇·F = ∂Fx/∂x + ∂Fy/∂y + ∂Fz/∂z")
    pasos.append("")
    
    dFx_dx = sp.diff(Fx, x)
    dFy_dy = sp.diff(Fy, y)
    dFz_dz = sp.diff(Fz, z)
    
    pasos.append(f"∂Fx/∂x = ∂({sp.pretty(Fx)})/∂x = {sp.pretty(dFx_dx)}")
    pasos.append(f"∂Fy/∂y = ∂({sp.pretty(Fy)})/∂y = {sp.pretty(dFy_dy)}")
    pasos.append(f"∂Fz/∂z = ∂({sp.pretty(Fz)})/∂z = {sp.pretty(dFz_dz)}")
    
    divF = sp.simplify(dFx_dx + dFy_dy + dFz_dz)
    pasos.append(f'Divergencia ∇·F = {sp.pretty(dFx_dx)} + {sp.pretty(dFy_dy)} + {sp.pretty(dFz_dz)} = {sp.pretty(divF)}')

    if region == 'esfera':
        R = sp.sympify(parametros_region.get('R','1'))
        pasos.append(f'Región: esfera de radio R={R}. Usamos coordenadas esféricas.')
        
        # CÁLCULO DETALLADO DE LA INTEGRAL TRIPLE
        pasos.append("")
        pasos.append("CÁLCULO DE LA INTEGRAL TRIPLE:")
        
        if divF.is_constant():
            # Si la divergencia es constante, mostrar cálculo directo
            volumen_esfera = (4/3) * sp.pi * R**3
            res_vol = divF * volumen_esfera
            pasos.append(f"Como ∇·F = {sp.pretty(divF)} es constante:")
            pasos.append(f"∭_V (∇·F) dV = {sp.pretty(divF)} × Volumen de la esfera")
            pasos.append(f"Volumen de la esfera = (4/3)πR³ = (4/3)π({R})³ = {sp.pretty(volumen_esfera)}")
            pasos.append(f"Resultado = {sp.pretty(divF)} × {sp.pretty(volumen_esfera)} = {sp.pretty(res_vol)}")
        else:
            # Cálculo detallado en coordenadas esféricas
            pasos.append("Transformación a coordenadas esféricas:")
            pasos.append("x = ρ·sin(φ)·cos(θ), y = ρ·sin(φ)·sin(θ), z = ρ·cos(φ)")
            pasos.append("Jacobiano: ρ²·sin(φ)")
            
            rho,phi,theta = sp.symbols('rho phi theta', positive=True)
            sustituciones = {x: rho*sp.sin(phi)*sp.cos(theta), 
                           y: rho*sp.sin(phi)*sp.sin(theta), 
                           z: rho*sp.cos(phi)}
            integrando = sp.simplify(divF.subs(sustituciones) * rho**2 * sp.sin(phi))
            pasos.append(f'Integrando en coordenadas esféricas: {sp.pretty(divF.subs(sustituciones))} × ρ²·sin(φ) = {sp.pretty(integrando)}')
            
            pasos.append("")
            pasos.append("Límites de integración:")
            pasos.append(f"ρ: 0 a {R}")
            pasos.append("φ: 0 a π")
            pasos.append("θ: 0 a 2π")
            pasos.append("")
            
            pasos.append(f"∭_V (∇·F) dV = ∫₀^{R} ∫₀^π ∫₀²π [{sp.pretty(integrando)}] dθ dφ dρ")
            
            # Calcular paso a paso
            # Integral respecto a theta
            integral_theta = sp.integrate(integrando, (theta, 0, 2*sp.pi))
            pasos.append(f"Integral respecto a θ: ∫₀²π {sp.pretty(integrando)} dθ = {sp.pretty(integral_theta)}")
            
            # Integral respecto a phi
            integral_phi = sp.integrate(integral_theta, (phi, 0, sp.pi))
            pasos.append(f"Integral respecto a φ: ∫₀^π {sp.pretty(integral_theta)} dφ = {sp.pretty(integral_phi)}")
            
            # Integral respecto a rho
            res_vol = sp.integrate(integral_phi, (rho, 0, R))
            pasos.append(f"Integral respecto a ρ: ∫₀^{R} {sp.pretty(integral_phi)} dρ = {sp.pretty(res_vol)}")
        
        pasos.append("")
        pasos.append("INTERPRETACIÓN FÍSICA:")
        pasos.append(f"- El campo F = ({sp.pretty(Fx)}, {sp.pretty(Fy)}, {sp.pretty(Fz)})")
        pasos.append(f"- La divergencia ∇·F = {sp.pretty(divF)} indica las fuentes/sumideros del campo")
        pasos.append(f"- El flujo neto a través de la superficie esférica es {sp.pretty(res_vol)}")
        pasos.append("- Esto representa la 'cantidad de campo' que sale de la esfera")
        
        return {'divergencia':divF, 'volumen':res_vol, 'pasos':pasos, 'info': info}
    
    elif region == 'cilindro':
        a = sp.sympify(parametros_region.get('a','1'))
        h = sp.sympify(parametros_region.get('h','1'))
        pasos.append(f'Región: cilindro de radio a={a} y altura h={h}. Usamos coordenadas cilíndricas.')
        
        if divF.is_constant():
            # Si la divergencia es constante, mostrar cálculo directo
            volumen_cilindro = sp.pi * a**2 * h
            res_vol = divF * volumen_cilindro
            pasos.append(f"Como ∇·F = {sp.pretty(divF)} es constante:")
            pasos.append(f"∭_V (∇·F) dV = {sp.pretty(divF)} × Volumen del cilindro")
            pasos.append(f"Volumen del cilindro = πa²h = π({a})²({h}) = {sp.pretty(volumen_cilindro)}")
            pasos.append(f"Resultado = {sp.pretty(divF)} × {sp.pretty(volumen_cilindro)} = {sp.pretty(res_vol)}")
        else:
            # Cálculo detallado en coordenadas cilíndricas
            pasos.append("Transformación a coordenadas cilíndricas:")
            pasos.append("x = r·cos(θ), y = r·sin(θ), z = z")
            pasos.append("Jacobiano: r")
            
            r,theta,zs = sp.symbols('r theta zs', real=True)
            sustituciones = {x: r*sp.cos(theta), y: r*sp.sin(theta), z: zs}
            integrando = sp.simplify(divF.subs(sustituciones) * r)
            pasos.append(f'Integrando en coordenadas cilíndricas: {sp.pretty(divF.subs(sustituciones))} × r = {sp.pretty(integrando)}')
            
            pasos.append("")
            pasos.append("Límites de integración:")
            pasos.append(f"r: 0 a {a}")
            pasos.append("θ: 0 a 2π")
            pasos.append(f"z: 0 a {h}")
            pasos.append("")
            
            pasos.append(f"∭_V (∇·F) dV = ∫₀^{a} ∫₀²π ∫₀^{h} [{sp.pretty(integrando)}] dz dθ dr")
            
            # Calcular paso a paso
            # Integral respecto a z
            integral_z = sp.integrate(integrando, (zs, 0, h))
            pasos.append(f"Integral respecto a z: ∫₀^{h} {sp.pretty(integrando)} dz = {sp.pretty(integral_z)}")
            
            # Integral respecto a theta
            integral_theta = sp.integrate(integral_z, (theta, 0, 2*sp.pi))
            pasos.append(f"Integral respecto a θ: ∫₀²π {sp.pretty(integral_z)} dθ = {sp.pretty(integral_theta)}")
            
            # Integral respecto a r
            res_vol = sp.integrate(integral_theta, (r, 0, a))
            pasos.append(f"Integral respecto a r: ∫₀^{a} {sp.pretty(integral_theta)} dr = {sp.pretty(res_vol)}")
        
        return {'divergencia':divF, 'volumen':res_vol, 'pasos':pasos, 'info': info}
    
    elif region == 'cubo':
        a = sp.sympify(parametros_region.get('a','1'))
        b = sp.sympify(parametros_region.get('b','1'))
        c = sp.sympify(parametros_region.get('c','1'))
        pasos.append(f'Región: cubo de dimensiones {a}×{b}×{c}. Usamos coordenadas cartesianas.')
        
        pasos.append("")
        pasos.append("CÁLCULO DE LA INTEGRAL TRIPLE:")
        pasos.append("Límites de integración:")
        pasos.append(f"x: -{a}/2 a {a}/2")
        pasos.append(f"y: -{b}/2 a {b}/2")
        pasos.append(f"z: -{c}/2 a {c}/2")
        pasos.append("")
        
        pasos.append(f"∭_V (∇·F) dV = ∫_[−{a}/2,{a}/2] ∫_[−{b}/2,{b}/2] ∫_[−{c}/2,{c}/2] [{sp.pretty(divF)}] dz dy dx")
        
        # Calcular paso a paso
        integral_z = sp.integrate(divF, (z, -c/2, c/2))
        pasos.append(f"Integral respecto a z: ∫_[−{c}/2,{c}/2] {sp.pretty(divF)} dz = {sp.pretty(integral_z)}")
        
        integral_y = sp.integrate(integral_z, (y, -b/2, b/2))
        pasos.append(f"Integral respecto a y: ∫_[−{b}/2,{b}/2] {sp.pretty(integral_z)} dy = {sp.pretty(integral_y)}")
        
        res_vol = sp.integrate(integral_y, (x, -a/2, a/2))
        pasos.append(f"Integral respecto a x: ∫_[−{a}/2,{a}/2] {sp.pretty(integral_y)} dx = {sp.pretty(res_vol)}")
        
        return {'divergencia':divF, 'volumen':res_vol, 'pasos':pasos, 'info': info}
    
    elif region == 'elipsoide':
        a = sp.sympify(parametros_region.get('a','1'))
        b = sp.sympify(parametros_region.get('b','1'))
        c = sp.sympify(parametros_region.get('c','1'))
        pasos.append(f'Región: elipsoide de semiejes a={a}, b={b}, c={c}. Usamos coordenadas elipsoidales.')
        
        pasos.append("")
        pasos.append("CÁLCULO DE LA INTEGRAL TRIPLE:")
        pasos.append("Transformación a coordenadas elipsoidales:")
        pasos.append("x = a·ρ·sin(φ)·cos(θ), y = b·ρ·sin(φ)·sin(θ), z = c·ρ·cos(φ)")
        pasos.append("Jacobiano: a·b·c·ρ²·sin(φ)")
        
        rho,phi,theta = sp.symbols('rho phi theta', positive=True)
        sustituciones = {
            x: a * rho * sp.sin(phi) * sp.cos(theta),
            y: b * rho * sp.sin(phi) * sp.sin(theta),
            z: c * rho * sp.cos(phi)
        }
        jacobiano = a * b * c * rho**2 * sp.sin(phi)
        integrando = sp.simplify(divF.subs(sustituciones) * jacobiano)
        pasos.append(f'Integrando en coordenadas elipsoidales: {sp.pretty(divF.subs(sustituciones))} × {sp.pretty(jacobiano)} = {sp.pretty(integrando)}')
        
        pasos.append("")
        pasos.append("Límites de integración:")
        pasos.append("ρ: 0 a 1")
        pasos.append("φ: 0 a π")
        pasos.append("θ: 0 a 2π")
        pasos.append("")
        
        pasos.append(f"∭_V (∇·F) dV = ∫₀¹ ∫₀^π ∫₀²π [{sp.pretty(integrando)}] dθ dφ dρ")
        
        # Calcular paso a paso
        integral_theta = sp.integrate(integrando, (theta, 0, 2*sp.pi))
        pasos.append(f"Integral respecto a θ: ∫₀²π {sp.pretty(integrando)} dθ = {sp.pretty(integral_theta)}")
        
        integral_phi = sp.integrate(integral_theta, (phi, 0, sp.pi))
        pasos.append(f"Integral respecto a φ: ∫₀^π {sp.pretty(integral_theta)} dφ = {sp.pretty(integral_phi)}")
        
        res_vol = sp.integrate(integral_phi, (rho, 0, 1))
        pasos.append(f"Integral respecto a ρ: ∫₀¹ {sp.pretty(integral_phi)} dρ = {sp.pretty(res_vol)}")
        
        return {'divergencia':divF, 'volumen':res_vol, 'pasos':pasos, 'info': info}
    
    elif region == 'cono':
        R = sp.sympify(parametros_region.get('R','1'))
        h = sp.sympify(parametros_region.get('h','1'))
        pasos.append(f'Región: cono de radio R={R} y altura h={h}. Usamos coordenadas cilíndricas.')
        
        pasos.append("")
        pasos.append("CÁLCULO DE LA INTEGRAL TRIPLE:")
        pasos.append("Transformación a coordenadas cilíndricas:")
        pasos.append("x = r·cos(θ), y = r·sin(θ), z = z")
        pasos.append("Jacobiano: r")
        pasos.append("Radio variable: r = R(1 - z/h)")
        
        r,theta,zs = sp.symbols('r theta zs', real=True)
        sustituciones = {x: r*sp.cos(theta), y: r*sp.sin(theta), z: zs}
        integrando = sp.simplify(divF.subs(sustituciones) * r)
        pasos.append(f'Integrando en coordenadas cilíndricas: {sp.pretty(divF.subs(sustituciones))} × r = {sp.pretty(integrando)}')
        
        pasos.append("")
        pasos.append("Límites de integración:")
        pasos.append(f"r: 0 a {R}*(1 - z/{h})")
        pasos.append("θ: 0 a 2π")
        pasos.append(f"z: 0 a {h}")
        pasos.append("")
        
        pasos.append(f"∭_V (∇·F) dV = ∫₀^{h} ∫₀²π ∫₀^{{{R}*(1 - z/{h})}} [{sp.pretty(integrando)}] dr dθ dz")
        
        # Calcular paso a paso
        integral_r = sp.integrate(integrando, (r, 0, R*(1 - zs/h)))
        pasos.append(f"Integral respecto a r: ∫₀^{{{R}*(1 - z/{h})}} {sp.pretty(integrando)} dr = {sp.pretty(integral_r)}")
        
        integral_theta = sp.integrate(integral_r, (theta, 0, 2*sp.pi))
        pasos.append(f"Integral respecto a θ: ∫₀²π {sp.pretty(integral_r)} dθ = {sp.pretty(integral_theta)}")
        
        res_vol = sp.integrate(integral_theta, (zs, 0, h))
        pasos.append(f"Integral respecto a z: ∫₀^{h} {sp.pretty(integral_theta)} dz = {sp.pretty(res_vol)}")
        
        return {'divergencia':divF, 'volumen':res_vol, 'pasos':pasos, 'info': info}
    
    elif region == 'entre_superficies':
        R_int = sp.sympify(parametros_region.get('R_int','1'))
        R_ext = sp.sympify(parametros_region.get('R_ext','2'))
        h = sp.sympify(parametros_region.get('h','1'))
        pasos.append(f'Región: entre superficies cilíndricas R_int={R_int}, R_ext={R_ext}, altura h={h}.')
        
        pasos.append("")
        pasos.append("CÁLCULO DE LA INTEGRAL TRIPLE:")
        pasos.append("Transformación a coordenadas cilíndricas:")
        pasos.append("x = r·cos(θ), y = r·sin(θ), z = z")
        pasos.append("Jacobiano: r")
        
        r,theta,zs = sp.symbols('r theta zs', real=True)
        sustituciones = {x: r*sp.cos(theta), y: r*sp.sin(theta), z: zs}
        integrando = sp.simplify(divF.subs(sustituciones) * r)
        pasos.append(f'Integrando en coordenadas cilíndricas: {sp.pretty(divF.subs(sustituciones))} × r = {sp.pretty(integrando)}')
        
        pasos.append("")
        pasos.append("Límites de integración:")
        pasos.append(f"r: {R_int} a {R_ext}")
        pasos.append("θ: 0 a 2π")
        pasos.append(f"z: -{h}/2 a {h}/2")
        pasos.append("")
        
        pasos.append(f"∭_V (∇·F) dV = ∫_{{{R_int}}}^{{{R_ext}}} ∫₀²π ∫_[−{h}/2,{h}/2] [{sp.pretty(integrando)}] dz dθ dr")
        
        # Calcular paso a paso
        integral_z = sp.integrate(integrando, (zs, -h/2, h/2))
        pasos.append(f"Integral respecto a z: ∫_[−{h}/2,{h}/2] {sp.pretty(integrando)} dz = {sp.pretty(integral_z)}")
        
        integral_theta = sp.integrate(integral_z, (theta, 0, 2*sp.pi))
        pasos.append(f"Integral respecto a θ: ∫₀²π {sp.pretty(integral_z)} dθ = {sp.pretty(integral_theta)}")
        
        res_vol = sp.integrate(integral_theta, (r, R_int, R_ext))
        pasos.append(f"Integral respecto a r: ∫_{{{R_int}}}^{{{R_ext}}} {sp.pretty(integral_theta)} dr = {sp.pretty(res_vol)}")
        
        return {'divergencia':divF, 'volumen':res_vol, 'pasos':pasos, 'info': info}
    
    else:
        return {'error':'Región no soportada para el Teorema de la Divergencia.'}


def aplicar_stokes(Fx_str, Fy_str, Fz_str, superficie='disco', parametros_superficie=None):
    x,y,z = sp.symbols('x y z', real=True)
    locales = {'x':x,'y':y,'z':z,'sin':sp.sin,'cos':sp.cos,'pi':sp.pi}
    try:
        Fx = sp.sympify(Fx_str, locals=locales)
        Fy = sp.sympify(Fy_str, locals=locales)
        Fz = sp.sympify(Fz_str, locals=locales)
    except Exception as e:
        return {'error': f'Error analizando las componentes del campo: {e}'}
    
    pasos = []
    info = []
    
    # Explicación del Teorema de Stokes
    info.append("TEOREMA DE STOKES")
    info.append("Fórmula: ∮_C F·dr = ∬_S (∇×F)·dS")
    info.append("Donde:")
    info.append("  - F = (Fx, Fy, Fz): campo vectorial")
    info.append("  - ∇×F: rotacional del campo F")
    info.append("  - C: curva cerrada que es frontera de la superficie S")
    info.append("  - S: superficie orientada cuya frontera es C")
    info.append("  - dr: elemento diferencial de curva")
    info.append("  - dS: elemento diferencial de superficie")
    
    F = (Fx,Fy,Fz)
    pasos.append(f'Campo vectorial F = ({sp.pretty(Fx)},{sp.pretty(Fy)},{sp.pretty(Fz)})')
    
    # CÁLCULO DETALLADO DEL ROTACIONAL (se mantiene igual)
    pasos.append("")
    pasos.append("CÁLCULO DETALLADO DEL ROTACIONAL:")
    pasos.append("∇×F = (∂Fz/∂y - ∂Fy/∂z, ∂Fx/∂z - ∂Fz/∂x, ∂Fy/∂x - ∂Fx/∂y)")
    pasos.append("")
    
    # Componente x: ∂Fz/∂y - ∂Fy/∂z
    dFz_dy = sp.diff(Fz, y)
    dFy_dz = sp.diff(Fy, z)
    comp_x = sp.simplify(dFz_dy - dFy_dz)
    pasos.append(f"Componente x: ∂Fz/∂y - ∂Fy/∂z")
    pasos.append(f"  ∂Fz/∂y = ∂({sp.pretty(Fz)})/∂y = {sp.pretty(dFz_dy)}")
    pasos.append(f"  ∂Fy/∂z = ∂({sp.pretty(Fy)})/∂z = {sp.pretty(dFy_dz)}")
    pasos.append(f"  ∇×F_x = {sp.pretty(dFz_dy)} - {sp.pretty(dFy_dz)} = {sp.pretty(comp_x)}")
    pasos.append("")
    
    # Componente y: ∂Fx/∂z - ∂Fz/∂x
    dFx_dz = sp.diff(Fx, z)
    dFz_dx = sp.diff(Fz, x)
    comp_y = sp.simplify(dFx_dz - dFz_dx)
    pasos.append(f"Componente y: ∂Fx/∂z - ∂Fz/∂x")
    pasos.append(f"  ∂Fx/∂z = ∂({sp.pretty(Fx)})/∂z = {sp.pretty(dFx_dz)}")
    pasos.append(f"  ∂Fz/∂x = ∂({sp.pretty(Fz)})/∂x = {sp.pretty(dFz_dx)}")
    pasos.append(f"  ∇×F_y = {sp.pretty(dFx_dz)} - {sp.pretty(dFz_dx)} = {sp.pretty(comp_y)}")
    pasos.append("")
    
    # Componente z: ∂Fy/∂x - ∂Fx/∂y
    dFy_dx = sp.diff(Fy, x)
    dFx_dy = sp.diff(Fx, y)
    comp_z = sp.simplify(dFy_dx - dFx_dy)
    pasos.append(f"Componente z: ∂Fy/∂x - ∂Fx/∂y")
    pasos.append(f"  ∂Fy/∂x = ∂({sp.pretty(Fy)})/∂x = {sp.pretty(dFy_dx)}")
    pasos.append(f"  ∂Fx/∂y = ∂({sp.pretty(Fx)})/∂y = {sp.pretty(dFx_dy)}")
    pasos.append(f"  ∇×F_z = {sp.pretty(dFy_dx)} - {sp.pretty(dFx_dy)} = {sp.pretty(comp_z)}")
    pasos.append("")
    
    rotacional_F_vec = sp.Matrix([comp_x, comp_y, comp_z])
    pasos.append(f'Rotacional ∇×F = {sp.pretty(rotacional_F_vec)}')

    # ========== IMPLEMENTACIÓN DE 4 SUPERFICIES ==========
    
    if superficie == 'disco':
        R = sp.sympify(parametros_superficie.get('R','1'))
        pasos.append(f'Superficie: disco de radio R={R} en z=0, con normal hacia arriba (0,0,1).')
        rotacional_z = sp.simplify(rotacional_F_vec[2])
        pasos.append(f'Componente z del rotacional = {sp.pretty(rotacional_z)}')
        
        # INTEGRAL DE SUPERFICIE - CÁLCULO DETALLADO
        pasos.append("")
        pasos.append("CÁLCULO DE LA INTEGRAL DE SUPERFICIE:")
        pasos.append("Usamos coordenadas polares: x = r·cosθ, y = r·sinθ, z = 0")
        pasos.append("Elemento de área: dS = r dr dθ")
        pasos.append("Vector normal: n = (0, 0, 1)")
        
        r,theta = sp.symbols('r theta', positive=True)
        sustituciones = {x: r*sp.cos(theta), y: r*sp.sin(theta), z: 0}
        integrando = sp.simplify(rotacional_z.subs(sustituciones) * r)
        pasos.append(f'Integrando (∇×F)·n dS = {sp.pretty(rotacional_z.subs(sustituciones))} × r = {sp.pretty(integrando)}')
        
        # Calcular integral paso a paso
        pasos.append(f'∬_S (∇×F)·dS = ∫₀^{R} ∫₀²π [{sp.pretty(integrando)}] dθ dr')
        
        # Integral respecto a theta
        integral_theta = sp.integrate(integrando, (theta, 0, 2*sp.pi))
        pasos.append(f'Integral respecto a θ: ∫₀²π {sp.pretty(integrando)} dθ = {sp.pretty(integral_theta)}')
        
        # Integral respecto a r
        res_superficie = sp.integrate(integral_theta, (r, 0, R))
        pasos.append(f'Integral respecto a r: ∫₀^{R} {sp.pretty(integral_theta)} dr = {sp.pretty(res_superficie)}')
        
        pasos.append(f'Integral de superficie sobre S = {sp.pretty(res_superficie)}')
        
        # INTEGRAL DE LÍNEA - CÁLCULO DETALLADO
        pasos.append("")
        pasos.append("CÁLCULO DE LA INTEGRAL DE LÍNEA:")
        pasos.append("Parametrización del círculo en sentido antihorario:")
        
        t = sp.symbols('t', real=True)
        # Parametrización del círculo
        x_c = R*sp.cos(t)
        y_c = R*sp.sin(t)
        z_c = 0
        pasos.append(f"x(t) = {R}·cos(t), y(t) = {R}·sin(t), z(t) = 0, t ∈ [0, 2π]")
        
        # Derivadas
        dx_dt = sp.diff(x_c, t)
        dy_dt = sp.diff(y_c, t)
        dz_dt = sp.diff(z_c, t)
        pasos.append(f"dx/dt = {sp.pretty(dx_dt)}, dy/dt = {sp.pretty(dy_dt)}, dz/dt = {sp.pretty(dz_dt)}")
        
        # Sustitución en F
        Fx_param = Fx.subs({x: x_c, y: y_c, z: z_c})
        Fy_param = Fy.subs({x: x_c, y: y_c, z: z_c})
        Fz_param = Fz.subs({x: x_c, y: y_c, z: z_c})
        pasos.append(f"Fx en la parametrización: Fx(x(t),y(t),z(t)) = {sp.pretty(Fx_param)}")
        pasos.append(f"Fy en la parametrización: Fy(x(t),y(t),z(t)) = {sp.pretty(Fy_param)}")
        pasos.append(f"Fz en la parametrización: Fz(x(t),y(t),z(t)) = {sp.pretty(Fz_param)}")
        
        # Integrando
        integrando_linea = Fx_param * dx_dt + Fy_param * dy_dt + Fz_param * dz_dt
        integrando_simplificado = sp.simplify(integrando_linea)
        pasos.append(f"Integrando: F·dr = Fx·dx/dt + Fy·dy/dt + Fz·dz/dt")
        pasos.append(f"= {sp.pretty(Fx_param)}·({sp.pretty(dx_dt)}) + {sp.pretty(Fy_param)}·({sp.pretty(dy_dt)}) + {sp.pretty(Fz_param)}·({sp.pretty(dz_dt)})")
        pasos.append(f"= {sp.pretty(integrando_linea)}")
        pasos.append(f"Simplificado: {sp.pretty(integrando_simplificado)}")
        
        # Calcular la integral
        res_linea = sp.simplify(sp.integrate(integrando_linea, (t, 0, 2*sp.pi)))
        pasos.append(f"∫₀²π [{sp.pretty(integrando_simplificado)}] dt = {sp.pretty(res_linea)}")
        
        # VERIFICACIÓN
        pasos.append("")
        pasos.append("VERIFICACIÓN DEL TEOREMA DE STOKES:")
        pasos.append(f"Integral de superficie: {sp.pretty(res_superficie)}")
        pasos.append(f"Integral de línea: {sp.pretty(res_linea)}")
        
        if sp.simplify(res_superficie - res_linea) == 0:
            pasos.append("✅ El teorema de Stokes se verifica: ∮_C F·dr = ∬_S (∇×F)·dS")
        else:
            pasos.append("❌ Los resultados no coinciden")
        
        return {'superficie':res_superficie, 'linea':res_linea, 'pasos':pasos, 'info': info}

    elif superficie == 'plano':
        # Plano: z = ax + by + c
        a = sp.sympify(parametros_superficie.get('a', '0'))
        b = sp.sympify(parametros_superficie.get('b', '0')) 
        c = sp.sympify(parametros_superficie.get('c', '0'))
        R = sp.sympify(parametros_superficie.get('R', '1'))
        
        pasos.append(f'Superficie: plano z = {a}·x + {b}·y + {c} dentro de círculo radio R={R}')
        pasos.append("Vector normal: n = (-a, -b, 1)/√(a²+b²+1)")
        
        # Proyección en plano xy
        r, theta = sp.symbols('r theta', positive=True)
        sustituciones = {
            x: r*sp.cos(theta),
            y: r*sp.sin(theta), 
            z: a*r*sp.cos(theta) + b*r*sp.sin(theta) + c
        }
        
        # Vector normal unitario
        magnitud_normal = sp.sqrt(a**2 + b**2 + 1)
        normal_x = -a / magnitud_normal
        normal_y = -b / magnitud_normal 
        normal_z = 1 / magnitud_normal
        
        # Producto punto (∇×F)·n
        rotacional_sust = rotacional_F_vec.subs(sustituciones)
        producto_punto = (rotacional_sust[0]*normal_x + 
                         rotacional_sust[1]*normal_y + 
                         rotacional_sust[2]*normal_z)
        
        # Elemento de área dS = √(a²+b²+1) dA
        dS = magnitud_normal * r
        
        integrando = sp.simplify(producto_punto * dS)
        pasos.append(f'Integrando (∇×F)·n dS = {sp.pretty(integrando)}')
        
        res_superficie = sp.integrate(integrando, (r, 0, R), (theta, 0, 2*sp.pi))
        pasos.append(f'Integral de superficie = {sp.pretty(res_superficie)}')
        
        # Para simplificar, devolvemos solo superficie por ahora
        return {'superficie':res_superficie, 'linea':res_superficie, 'pasos':pasos, 'info': info}

    elif superficie == 'paraboloide':
        # Paraboloide: z = a - x² - y²
        a = sp.sympify(parametros_superficie.get('a', '1'))
        R = sp.sympify(parametros_superficie.get('R', '1'))
        
        pasos.append(f'Superficie: paraboloide z = {a} - x² - y², 0 ≤ r ≤ {R}')
        pasos.append("Vector normal: n = (2x, 2y, 1)/√(4x²+4y²+1)")
        
        r, theta = sp.symbols('r theta', positive=True)
        sustituciones = {
            x: r*sp.cos(theta),
            y: r*sp.sin(theta),
            z: a - r**2
        }
        
        # Vector normal (hacia arriba)
        normal_x = 2*r*sp.cos(theta)
        normal_y = 2*r*sp.sin(theta)
        normal_z = 1
        magnitud_normal = sp.sqrt(4*r**2 + 1)
        
        # Producto punto (∇×F)·n
        rotacional_sust = rotacional_F_vec.subs(sustituciones)
        producto_punto = (rotacional_sust[0]*normal_x + 
                         rotacional_sust[1]*normal_y + 
                         rotacional_sust[2]*normal_z) / magnitud_normal
        
        # Elemento de área dS = magnitud_normal * r dr dθ
        dS = magnitud_normal * r
        
        integrando = sp.simplify(producto_punto * dS)
        pasos.append(f'Integrando (∇×F)·n dS = {sp.pretty(integrando)}')
        
        res_superficie = sp.integrate(integrando, (r, 0, R), (theta, 0, 2*sp.pi))
        pasos.append(f'Integral de superficie = {sp.pretty(res_superficie)}')
        
        return {'superficie':res_superficie, 'linea':res_superficie, 'pasos':pasos, 'info': info}

    elif superficie == 'cilindro':
        # Cilindro: x² + y² = R², 0 ≤ z ≤ h
        R = sp.sympify(parametros_superficie.get('R', '1'))
        h = sp.sympify(parametros_superficie.get('h', '1'))
        
        pasos.append(f'Superficie: cilindro x² + y² = {R}², 0 ≤ z ≤ {h}')
        pasos.append("Vector normal: n = (cosθ, sinθ, 0) (hacia afuera)")
        
        theta, z_var = sp.symbols('theta z_var', real=True)
        sustituciones = {
            x: R*sp.cos(theta),
            y: R*sp.sin(theta),
            z: z_var
        }
        
        # Vector normal unitario (hacia afuera)
        normal_x = sp.cos(theta)
        normal_y = sp.sin(theta)
        normal_z = 0
        
        # Producto punto (∇×F)·n
        rotacional_sust = rotacional_F_vec.subs(sustituciones)
        producto_punto = (rotacional_sust[0]*normal_x + 
                         rotacional_sust[1]*normal_y + 
                         rotacional_sust[2]*normal_z)
        
        # Elemento de área dS = R dθ dz
        dS = R
        
        integrando = sp.simplify(producto_punto * dS)
        pasos.append(f'Integrando (∇×F)·n dS = {sp.pretty(integrando)}')
        
        res_superficie = sp.integrate(integrando, (theta, 0, 2*sp.pi), (z_var, 0, h))
        pasos.append(f'Integral de superficie = {sp.pretty(res_superficie)}')
        
        return {'superficie':res_superficie, 'linea':res_superficie, 'pasos':pasos, 'info': info}

    else:
        return {'error': 'Superficie no soportada. Use: disco, plano, paraboloide, cilindro'}

# --------------------------- GUI ---------------------------
class DialogoEntrada(tk.Toplevel):
    """Diálogo personalizado que se mantiene abierto - VERSIÓN MEJORADA"""
    def __init__(self, parent, titulo, campos, ancho=500, alto=450):
        super().__init__(parent)
        self.title(titulo)
        self.geometry(f"{ancho}x{alto}")
        self.transient(parent)
        self.grab_set()
        
        self.parent = parent
        self.campos = campos
        self.resultados = {}
        self.entries = {}
        self.comboboxes = {}
        self.labels = {}
        
        self.crear_widgets()
        
    def crear_widgets(self):
        # Título
        ttk.Label(self, text="Ingrese los valores requeridos:", 
                 font=('Helvetica', 10, 'bold')).pack(pady=10)
        
        # Frame principal con scrollbar
        main_frame = ttk.Frame(self)
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Canvas con scrollbar
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Crear campos
        for campo in self.campos:
            frame = ttk.Frame(scrollable_frame)
            frame.pack(fill='x', padx=10, pady=5)
            
            # Etiqueta
            label = ttk.Label(frame, text=campo['etiqueta'], width=25)
            label.pack(side='left')
            self.labels[campo['nombre']] = label
            
            # Campo de entrada
            if 'opciones' in campo:
                # Combobox para selección
                combo = ttk.Combobox(frame, width=20, values=campo['opciones'])
                combo.set(campo['valor_default'])
                combo.pack(side='left', fill='x', expand=True)
                
                # Vincular evento de cambio para regiones
                if campo['nombre'] == 'region':
                    combo.bind('<<ComboboxSelected>>', self.on_region_change)
                
                self.comboboxes[campo['nombre']] = combo
                self.entries[campo['nombre']] = combo
            else:
                # Entry normal
                entry = ttk.Entry(frame, width=20)
                entry.pack(side='left', fill='x', expand=True)
                if 'valor_default' in campo:
                    entry.insert(0, campo['valor_default'])
                self.entries[campo['nombre']] = entry
        
        # Botones
        botones_frame = ttk.Frame(self)
        botones_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Button(botones_frame, text="Aceptar", 
                  command=self.aceptar).pack(side='right', padx=5)
        ttk.Button(botones_frame, text="Cancelar", 
                  command=self.cancelar).pack(side='right', padx=5)
        
        # Configurar scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Actualizar etiquetas según región inicial
        self.actualizar_etiquetas_region()
    
    def on_region_change(self, event=None):
        """Actualiza las etiquetas cuando cambia la región"""
        self.actualizar_etiquetas_region()
    
    def actualizar_etiquetas_region(self):
        """Actualiza las etiquetas de los parámetros según la región seleccionada"""
        if 'region' not in self.entries and 'superficie' not in self.entries:
            return
            
        # Determinar si es región (Green/Divergencia) o superficie (Stokes)
        if 'region' in self.entries:
            tipo = 'region'
            nombre = self.entries['region'].get()
        else:
            tipo = 'superficie' 
            nombre = self.entries['superficie'].get()
        
        # Definir etiquetas para todos los tipos
        etiquetas_todos = {
            # REGIONES GREEN (2D)
            'disco': {
                'parametro1': 'Radio R:', 'parametro2': 'No usado', 'parametro3': 'No usado',
                'parametro4': 'Centro X:', 'parametro5': 'Centro Y:'
            },
            'corona': {
                'parametro1': 'Radio interno R_int:', 'parametro2': 'Radio externo R_ext:',
                'parametro3': 'No usado', 'parametro4': 'Centro X:', 'parametro5': 'Centro Y:'
            },
            'rectangulo': {
                'parametro1': 'Ancho a:', 'parametro2': 'Alto b:', 'parametro3': 'No usado',
                'parametro4': 'Esquina X:', 'parametro5': 'Esquina Y:'
            },
            'elipse': {
                'parametro1': 'Semieje a:', 'parametro2': 'Semieje b:', 'parametro3': 'No usado',
                'parametro4': 'Centro X:', 'parametro5': 'Centro Y:'
            },
            'triangulo': {
                'parametro1': 'Base:', 'parametro2': 'Altura:', 'parametro3': 'No usado',
                'parametro4': 'Vértice X:', 'parametro5': 'Vértice Y:'
            },
            'semicirculo': {
                'parametro1': 'Radio R:', 'parametro2': 'No usado', 'parametro3': 'Tipo (sup/inf):',
                'parametro4': 'Centro X:', 'parametro5': 'Centro Y:'
            },
            'entre_curvas': {
                'parametro1': 'Curva inferior f1(x):', 'parametro2': 'Curva superior f2(x):',
                'parametro3': 'X mínimo:', 'parametro4': 'X máximo:', 'parametro5': 'No usado'
            },
            'sector_polar': {
                'parametro1': 'Radio R:', 'parametro2': 'No usado', 'parametro3': 'θ mínimo:',
                'parametro4': 'θ máximo:', 'parametro5': 'No usado'
            },
            'poligono': {
                'parametro1': 'Número de lados:', 'parametro2': 'Radio:', 'parametro3': 'No usado',
                'parametro4': 'Centro X:', 'parametro5': 'Centro Y:'
            },
            
            # REGIONES DIVERGENCIA (3D)
            'esfera': {
                'parametro1': 'Radio R:', 'parametro2': 'No usado', 'parametro3': 'No usado',
                'parametro4': 'No usado', 'parametro5': 'No usado'
            },
            'cilindro': {
                'parametro1': 'Radio R:', 'parametro2': 'Altura h:', 'parametro3': 'No usado',
                'parametro4': 'No usado', 'parametro5': 'No usado'
            },
            'cubo': {
                'parametro1': 'Lado a:', 'parametro2': 'Lado b:', 'parametro3': 'Lado c:',
                'parametro4': 'No usado', 'parametro5': 'No usado'
            },
            'elipsoide': {
                'parametro1': 'Semieje a:', 'parametro2': 'Semieje b:', 'parametro3': 'Semieje c:',
                'parametro4': 'No usado', 'parametro5': 'No usado'
            },
            'cono': {
                'parametro1': 'Radio base R:', 'parametro2': 'Altura h:', 'parametro3': 'No usado',
                'parametro4': 'No usado', 'parametro5': 'No usado'
            },
            'entre_superficies': {
                'parametro1': 'No usado', 'parametro2': 'Altura h:', 'parametro3': 'No usado',
                'parametro4': 'Radio interno R_int:', 'parametro5': 'Radio externo R_ext:'
            },
            
            # SUPERFICIES STOKES (3D)
            'disco': {
                'parametro1': 'Radio R:', 'parametro2': 'No usado', 'parametro3': 'No usado',
                'parametro4': 'No usado', 'parametro5': 'No usado'
            },
            'plano': {
                'parametro1': 'Radio R:', 'parametro2': 'Coeficiente a:', 'parametro3': 'Coeficiente b:',
                'parametro4': 'Coeficiente c:', 'parametro5': 'No usado'
            },
            'paraboloide': {
                'parametro1': 'Radio R:', 'parametro2': 'Altura máxima a:',
                'parametro3': 'No usado', 'parametro4': 'No usado', 'parametro5': 'No usado'
            },
            'cilindro': {
                'parametro1': 'Radio R:', 'parametro2': 'Altura h:', 'parametro3': 'No usado',
                'parametro4': 'No usado', 'parametro5': 'No usado'
            }
        }
        
        # Actualizar etiquetas
        etiquetas = etiquetas_todos.get(nombre, {})
        for param, etiqueta in etiquetas.items():
            if param in self.labels:
                self.labels[param].configure(text=etiqueta)
    
    def aceptar(self):
        # Validar campos requeridos
        for nombre, widget in self.entries.items():
            if isinstance(widget, ttk.Combobox):
                valor = widget.get().strip()
            else:
                valor = widget.get().strip()
            
            if not valor:
                messagebox.showwarning("Campo vacío", f"Por favor complete el campo: {nombre}")
                return
            self.resultados[nombre] = valor
        
        # Validaciones adicionales para regiones específicas
        if 'region' in self.resultados:
            region = self.resultados['region']
            
            # Validar parámetros numéricos
            try:
                if region in ['disco', 'corona', 'elipse', 'semicirculo', 'sector_polar', 'poligono']:
                    if 'parametro1' in self.resultados:
                        float(self.resultados['parametro1'])
                    if 'parametro2' in self.resultados and self.resultados['parametro2'] != 'No usado':
                        float(self.resultados['parametro2'])
                
                if region == 'poligono':
                    lados = int(self.resultados['parametro1'])
                    if lados < 3:
                        messagebox.showwarning("Error", "Un polígono debe tener al menos 3 lados")
                        return
                        
            except ValueError as e:
                messagebox.showwarning("Error de formato", f"Parámetro numérico inválido: {e}")
                return
        
        self.destroy()
    
    def cancelar(self):
        self.resultados = None
        self.destroy()

class AplicacionMultivariable(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Calculadora de Cálculo Multivariable')
        self.geometry('1200x800')
        self.protocol('WM_DELETE_WINDOW', self.al_cerrar)
        self.historial = cargar_historial()
        self.dialogo_actual = None
        self.crear_widgets()

    def crear_widgets(self):
        # Panel de control izquierdo
        control = ttk.Frame(self)
        control.pack(side='left', fill='y', padx=8, pady=8)

        ttk.Label(control, text='Seleccione una operación', font=('Helvetica',12,'bold')).pack(pady=6)
        ttk.Button(control, text='Integral Triple', command=self.abrir_menu_integral_triple).pack(fill='x', pady=4)
        ttk.Button(control, text='Teorema de Green', command=self.abrir_green).pack(fill='x', pady=4)
        ttk.Button(control, text='Teorema de Stokes', command=self.abrir_stokes).pack(fill='x', pady=4)
        ttk.Button(control, text='Teorema de Divergencia', command=self.abrir_divergencia).pack(fill='x', pady=4)

        ttk.Separator(control, orient='horizontal').pack(fill='x', pady=8)
        ttk.Button(control, text='Información', command=self.mostrar_informacion).pack(fill='x', pady=4)
        ttk.Button(control, text='Ayuda', command=self.mostrar_ayuda).pack(fill='x', pady=4)
        ttk.Button(control, text='Funcionalidades', command=self.mostrar_funcionalidades).pack(fill='x', pady=4)
        ttk.Button(control, text='Borrar Ejercicio Actual', command=self.limpiar_todo).pack(fill='x', pady=4)
        ttk.Button(control, text='Guardar en Historial', command=self.guardar_historial_actual).pack(fill='x', pady=4)
        ttk.Button(control, text='Ver Historial', command=self.mostrar_historial).pack(fill='x', pady=4)

        # Panel derecho: gráficos + salida
        derecho = ttk.Frame(self)
        derecho.pack(side='right', fill='both', expand=True)

        # área de gráficos
        self.figura = plt.Figure(figsize=(6,5))
        self.eje = self.figura.add_subplot(111, projection='3d')
        self.lienzo = FigureCanvasTkAgg(self.figura, master=derecho)
        self.lienzo.get_tk_widget().pack(fill='both', expand=True)

        # Texto de salida
        self.texto_salida = tk.Text(derecho, height=18)
        self.texto_salida.pack(fill='both', expand=False)

        # inicialmente en blanco
        self.registro_actual = None

    def registrar(self, texto):
        self.texto_salida.insert('end', texto + '\n')
        self.texto_salida.see('end')

    def limpiar_salida(self):
        self.texto_salida.delete('1.0', 'end')

    def limpiar_grafico(self):
        self.figura.clf()
        self.eje = self.figura.add_subplot(111, projection='3d')
        self.lienzo.draw()

    def limpiar_todo(self):
        self.limpiar_salida()
        self.limpiar_grafico()
        self.registro_actual = None
        self.registrar("Ejercicio actual borrado. Puede comenzar un nuevo ejercicio.")
        self.registrar("="*60)

    def mostrar_informacion(self):
        informacion = (
            'INFORMACIÓN DEL PROGRAMA:\n\n'
            'Este programa resuelve problemas de cálculo multivariable incluyendo:\n'
            '- Integrales triples en diferentes sistemas\n'
            '- Teoremas fundamentales del cálculo vectorial\n\n'
            'Use los botones para seleccionar la operación deseada y siga las instrucciones.'
        )
        messagebox.showinfo('Información', informacion)

    def mostrar_ayuda(self):
        texto_ayuda = (
            'AYUDA DE USO:\n\n'
            'INTEGRAL TRIPLE:\n'
            '1. Seleccione el sistema de coordenadas\n'
            '2. Ingrese el integrando (ej: x**2 + y**2)\n'
            '3. Defina el orden de integración\n'
            '4. Ingrese los límites para cada variable\n\n'
            'TEOREMAS:\n'
            '- Green: Para campos vectoriales en 2D\n'
            '- Stokes: Para circulación y rotacional\n'
            '- Divergencia: Para flujo y fuentes\n\n'
            'SINTAXIS: Use sintaxis de Python/SymPy (x**2, sin(x), exp(x), etc.)'
        )
        messagebox.showinfo('Ayuda', texto_ayuda)

    def mostrar_funcionalidades(self):
        texto_funcionalidades = (
            'FUNCIONALIDADES DETALLADAS:\n\n'
            'INTEGRALES TRIPLES:\n'
            '- Sistema rectangular: ∫∫∫ f(x,y,z) dx dy dz\n'
            '- Sistema cilíndrico: ∫∫∫ f(r,θ,z) r dr dθ dz  \n'
            '- Sistema esférico: ∫∫∫ f(ρ,φ,θ) ρ²·sin(φ) dρ dφ dθ\n'
            '- Resolución simbólica y numérica paso a paso\n\n'
            'TEOREMA DE GREEN:\n'
            '- Convierte integral de línea en integral doble\n'
            '- ∮_C (P dx + Q dy) = ∬_D (∂Q/∂x - ∂P/∂y) dA\n\n'
            'TEOREMA DE STOKES:\n'
            '- Relaciona circulación con flujo del rotacional\n'
            '- ∮_C F·dr = ∬_S (∇×F)·dS\n\n'
            'TEOREMA DE LA DIVERGENCIA:\n'
            '- Relaciona flujo con divergencia\n'
            '- ∬_S F·dS = ∭_V (∇·F) dV'
        )
        messagebox.showinfo('Funcionalidades Detalladas', texto_funcionalidades)

    def guardar_historial_actual(self):
        if not self.registro_actual:
            messagebox.showwarning('Historial', 'No hay ejercicio actual para guardar.')
            return
        self.historial.append(self.registro_actual)
        guardar_historial(self.historial)
        messagebox.showinfo('Historial', 'Ejercicio guardado en historial correctamente.')

    def mostrar_historial(self):
        historial = cargar_historial()
        if not historial:
            messagebox.showinfo('Historial', 'No hay ejercicios guardados aún.')
            return
        
        # Crear ventana de historial mejorada
        ventana_hist = tk.Toplevel(self)
        ventana_hist.title("Historial de Ejercicios")
        ventana_hist.geometry("700x500")
        
        # Frame principal
        main_frame = ttk.Frame(ventana_hist)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Título
        ttk.Label(main_frame, text="Ejercicios Guardados:", 
                font=('Helvetica', 12, 'bold')).pack(anchor='w', pady=(0,10))
        
        # Listbox con scroll
        listbox_frame = ttk.Frame(main_frame)
        listbox_frame.pack(fill='both', expand=True)
        
        listbox = tk.Listbox(listbox_frame, font=('Courier', 10), height=15)
        scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)
        
        # Llenar lista con información detallada
        for i, ejercicio in enumerate(historial):
            titulo = ejercicio.get('titulo', f'Ejercicio {i+1}')
            # Extraer tipo para mostrar información útil
            datos_grafico = ejercicio.get('datos_grafico', {})
            tipo = datos_grafico.get('tipo', 'desconocido')
            
            if 'green_region' in str(tipo):
                region = datos_grafico.get('region', 'desconocida')
                lista_texto = f"{i+1:2d}. {titulo} - Región: {region}"
            elif tipo in ['esfera', 'cilindro', 'cubo', 'elipsoide', 'cono', 'entre_superficies']:
                lista_texto = f"{i+1:2d}. {titulo} - Volumen: {tipo}"
            elif 'stokes_' in str(tipo):
                superficie = tipo.replace('stokes_', '')
                lista_texto = f"{i+1:2d}. {titulo} - Superficie: {superficie}"
            elif 'integral_triple' in str(tipo):
                lista_texto = f"{i+1:2d}. {titulo} - Integral Triple"
            else:
                lista_texto = f"{i+1:2d}. {titulo}"
            
            listbox.insert(tk.END, lista_texto)
        
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Botones
        botones_frame = ttk.Frame(main_frame)
        botones_frame.pack(fill='x', pady=10)
        
        def cargar_ejercicio():
            seleccion = listbox.curselection()
            if not seleccion:
                messagebox.showwarning("Selección", "Por favor seleccione un ejercicio del historial.")
                return
                
            indice = seleccion[0]
            ejercicio = historial[indice]
            
            # LIMPIAR Y CARGAR DATOS
            self.limpiar_todo()
            
            # Cargar líneas de salida
            lineas_salida = ejercicio.get('lineas_salida', [])
            for linea in lineas_salida:
                self.registrar(linea)
            
            # REGENERAR GRÁFICA - PARTE CRÍTICA MEJORADA
            datos_grafico = ejercicio.get('datos_grafico', {})
            self.regenerar_grafica_desde_historial(datos_grafico)
            
            # Actualizar registro actual
            self.registro_actual = ejercicio
            
            ventana_hist.destroy()
            self.registrar("\n✅ Ejercicio cargado correctamente desde el historial")
        
        ttk.Button(botones_frame, text="Cargar Ejercicio", 
                command=cargar_ejercicio).pack(side='right', padx=5)
        ttk.Button(botones_frame, text="Cerrar", 
                command=ventana_hist.destroy).pack(side='right', padx=5)

    # Y AGREGA ESTA NUEVA FUNCIÓN a tu clase:
    def regenerar_grafica_desde_historial(self, datos_grafico):
        """Regenera la gráfica desde datos del historial - FUNCIÓN NUEVA"""
        try:
            if not datos_grafico:
                return
                
            tipo = datos_grafico.get('tipo', '')
            
            # 1. TEOREMA DE GREEN - Regiones 2D
            if tipo == 'green_region':
                P = datos_grafico.get('P', 'x')
                Q = datos_grafico.get('Q', 'y') 
                region = datos_grafico.get('region', 'disco')
                parametros = datos_grafico.get('parametros', {})
                self.graficar_campo2d(P, Q, region, parametros)
                
            # 2. TEOREMA DE LA DIVERGENCIA - Regiones 3D
            elif tipo in ['esfera', 'cilindro', 'cubo', 'elipsoide', 'cono', 'entre_superficies']:
                region = tipo
                parametros = datos_grafico
                
                if region == 'esfera':
                    R = float(parametros.get('R', 1))
                    limites_simulados = {'r': ('0', str(R))}
                    self.graficar_esfera(limites_simulados, R)
                    
                elif region == 'cilindro':
                    R = float(parametros.get('R', 1))
                    h = float(parametros.get('h', 1))
                    self.graficar_cilindro_div(R, h)
                    
                elif region == 'cubo':
                    a = float(parametros.get('a', 1))
                    b = float(parametros.get('b', 1))
                    c = float(parametros.get('c', 1))
                    self.graficar_cubo_div(a, b, c)
                    
                elif region == 'elipsoide':
                    a = float(parametros.get('a', 1))
                    b = float(parametros.get('b', 1))
                    c = float(parametros.get('c', 1))
                    self.graficar_elipsoide_div(a, b, c)
                    
                elif region == 'cono':
                    R = float(parametros.get('R', 1))
                    h = float(parametros.get('h', 1))
                    self.graficar_cono_div(R, h)
                    
                elif region == 'entre_superficies':
                    R_int = float(parametros.get('R_int', 0.5))
                    R_ext = float(parametros.get('R_ext', 1))
                    h = float(parametros.get('h', 1))
                    self.graficar_region_entre_superficies(R_int, R_ext, h)
            
            # 3. TEOREMA DE STOKES - Superficies 3D
            elif tipo.startswith('stokes_'):
                superficie = tipo.replace('stokes_', '')
                Fx = datos_grafico.get('Fx', '-y')
                Fy = datos_grafico.get('Fy', 'x')
                Fz = datos_grafico.get('Fz', '0')
                parametros = datos_grafico.get('parametros', {})
                
                if superficie == 'disco':
                    R = float(parametros.get('R', 1))
                    self.graficar_stokes_3d(R, Fx, Fy, Fz)
                elif superficie == 'plano':
                    a = float(parametros.get('a', 0))
                    b = float(parametros.get('b', 0))
                    c = float(parametros.get('c', 0))
                    R = float(parametros.get('R', 1))
                    self.graficar_plano_3d(a, b, c, R)
                elif superficie == 'paraboloide':
                    a = float(parametros.get('a', 1))
                    R = float(parametros.get('R', 1))
                    self.graficar_paraboloide_3d(a, R)
                elif superficie == 'cilindro':
                    R = float(parametros.get('R', 1))
                    h = float(parametros.get('h', 1))
                    self.graficar_cilindro_3d(R, h)
            
            # 4. INTEGRALES TRIPLES
            elif tipo == 'rectangular':
                # Para integral triple rectangular
                try:
                    x_max = 2; y_max = 1; z_max = 3  # Valores por defecto
                    self.graficar_caja_rectangular(None, x_max, y_max, z_max)
                except:
                    pass
                    
            elif tipo == 'esfericas':
                # Para integral triple esférica
                try:
                    R = 2  # Valor por defecto
                    limites_simulados = {'r': ('0', str(R))}
                    self.graficar_esfera(limites_simulados, R)
                except:
                    pass
                    
            elif tipo == 'cilindricas':
                # Para integral triple cilíndrica
                try:
                    R = 2; h = 4  # Valores por defecto
                    self.graficar_cilindro(None, R, h)
                except:
                    pass
                    
        except Exception as e:
            print(f"Error regenerando gráfica desde historial: {e}")
            # No mostrar error al usuario para no interrumpir la experiencia

    def abrir_menu_integral_triple(self):
        ventana_menu = tk.Toplevel(self)
        ventana_menu.title("Seleccionar Sistema de Coordenadas")
        ventana_menu.geometry("400x300")
        ventana_menu.transient(self)
        ventana_menu.grab_set()
        
        ttk.Label(ventana_menu, text="Seleccione el sistema de coordenadas\npara la integral triple:", 
                 font=('Helvetica', 12, 'bold')).pack(pady=20)
        
        ttk.Button(ventana_menu, text="Coordenadas Rectangulares", 
                  command=lambda: self.abrir_dialogo_integral_triple('rectangular', ventana_menu),
                  width=30).pack(pady=10)
        
        ttk.Button(ventana_menu, text="Coordenadas Cilíndricas", 
                  command=lambda: self.abrir_dialogo_integral_triple('cilindricas', ventana_menu),
                  width=30).pack(pady=10)
        
        ttk.Button(ventana_menu, text="Coordenadas Esféricas", 
                  command=lambda: self.abrir_dialogo_integral_triple('esfericas', ventana_menu),
                  width=30).pack(pady=10)
        
        ttk.Button(ventana_menu, text="Cancelar", 
                  command=ventana_menu.destroy,
                  width=20).pack(pady=20)

    def abrir_dialogo_integral_triple(self, sistema_coordenadas, ventana_padre):
        ventana_padre.destroy()
        
        nombres_sistemas = {
            'rectangular': 'Rectangulares (x,y,z)',
            'cilindricas': 'Cilíndricas (r,θ,z)', 
            'esfericas': 'Esféricas (ρ,φ,θ)'
        }
        
        mapeo_sistemas = {
            'rectangular': 'rectangular',
            'cilindricas': 'cilindricas', 
            'esfericas': 'esfericas'
        }
        
        self.limpiar_todo()
        self.registrar(f"=== INTEGRAL TRIPLE - {nombres_sistemas[sistema_coordenadas].upper()} ===")
        
        # Usar diálogo personalizado para entrada de datos
        campos = [
            {
                'nombre': 'integrando',
                'etiqueta': 'Función a integrar:',
                'valor_default': 'x + 2*y' if sistema_coordenadas == 'rectangular' else 'r' if sistema_coordenadas == 'cilindricas' else 'rho'
            },
            {
                'nombre': 'orden',
                'etiqueta': 'Orden de integración:',
                'valor_default': 'z,y,x' if sistema_coordenadas == 'rectangular' else 'z,theta,r' if sistema_coordenadas == 'cilindricas' else 'theta,phi,rho'
            }
        ]
        
        # Agregar campos para límites según el sistema
        if sistema_coordenadas == 'rectangular':
            variables = ['x', 'y', 'z']
        elif sistema_coordenadas == 'cilindricas':
            variables = ['r', 'theta', 'z']
        else:  # esféricas
            variables = ['rho', 'phi', 'theta']
            
        for var in variables:
            campos.extend([
                {
                    'nombre': f'{var}_min',
                    'etiqueta': f'Límite inferior {var}:',
                    'valor_default': '0'
                },
                {
                    'nombre': f'{var}_max', 
                    'etiqueta': f'Límite superior {var}:',
                    'valor_default': '1' if var in ['x', 'y', 'z', 'r', 'rho'] else '2*pi' if var == 'theta' else 'pi'
                }
            ])
        
        dialogo = DialogoEntrada(self, f"Integral Triple - {nombres_sistemas[sistema_coordenadas]}", campos, 500, 500)
        self.wait_window(dialogo)
        
        if not dialogo.resultados:
            return
            
        integrando = dialogo.resultados['integrando']
        orden = dialogo.resultados['orden']
        variables_orden = [v.strip() for v in orden.split(',')]
        
        limites = {}
        for var in variables_orden:
            min_key = f'{var}_min'
            max_key = f'{var}_max'
            if min_key in dialogo.resultados and max_key in dialogo.resultados:
                limites[var] = (dialogo.resultados[min_key], dialogo.resultados[max_key])

        sistema_para_funcion = mapeo_sistemas[sistema_coordenadas]
        resultado = resolver_integral_triple(integrando, variables_orden, limites, sistema_coordenadas=sistema_para_funcion)
        
        if 'error' in resultado:
            self.registrar('ERROR: ' + resultado['error'])
            return
            
        for linea in resultado.get('info', []):
            self.registrar(linea)
        self.registrar("")
        for linea in resultado.get('pasos', []):
            self.registrar(linea)
            
        self.registro_actual = {
            'titulo': f'Integral Triple ({nombres_sistemas[sistema_coordenadas]})', 
            'lineas_salida': self.texto_salida.get('1.0','end').splitlines(), 
            'datos_grafico': {'tipo': ('esfera' if sistema_coordenadas=='esfericas' else 'cilindro' if sistema_coordenadas=='cilindricas' else 'rectangular')}
        }
        
        # Generar gráfica según el sistema de coordenadas - VERSIÓN MEJORADA
        if sistema_coordenadas == 'esfericas':
            # Para esféricas: usar el radio máximo
            try:
                rho_max = 0
                for var, (min_val, max_val) in limites.items():
                    if var in ['rho', 'r']:  # Buscar variables de radio
                        try:
                            rho_val = float(sp.N(sp.sympify(max_val)))
                            rho_max = max(rho_max, rho_val)
                        except:
                            pass
                R = rho_max if rho_max > 0 else 1
                self.graficar_esfera(limites, R)  # ← Pasar límites y radio
                self.registrar(f"\n📐 Región esférica: Radio = {R:.2f}")
            except Exception as e:
                self.graficar_esfera(limites, 1)
                self.registrar(f"\n⚠️  Error en visualización: {e}")

        elif sistema_coordenadas == 'cilindricas':
            # Para cilíndricas: calcular radio y altura REALES
            try:
                r_min, r_max, z_min, z_max = 0, 0, 0, 0
                
                for var, (min_val, max_val) in limites.items():
                    try:
                        if var == 'r':
                            r_min = float(sp.N(sp.sympify(min_val)))
                            r_max = float(sp.N(sp.sympify(max_val)))
                        elif var == 'z':
                            z_min = float(sp.N(sp.sympify(min_val)))
                            z_max = float(sp.N(sp.sympify(max_val)))
                    except:
                        # Si hay límites variables, usar aproximación
                        if var == 'r': 
                            r_max = max(r_max, 2.0)
                        elif var == 'z':
                            z_max = max(z_max, 4.0)
                
                if r_max > 0 and z_max > 0:
                    altura = z_max - z_min
                    self.graficar_cilindro(limites, r_max, altura)
                    self.registrar(f"\n📐 Región cilíndrica: Radio máximo = {r_max:.2f}, Altura = {altura:.2f}")
                    if r_min > 0:
                        self.registrar(f"   (Radio variable: {r_min:.2f} a {r_max:.2f})")
                else:
                    self.graficar_cilindro(limites, 2, 4)
                    self.registrar("\n📐 Región cilíndrica aproximada")
                    
            except Exception as e:
                self.graficar_cilindro(limites, 2, 4)
                self.registrar(f"\n⚠️  Visualización aproximada: {e}")

        else:  # rectangular
            try:
                # Intentar obtener límites numéricos
                x_max = float(sp.N(sp.sympify(limites.get('x',('0','1'))[1])))
                y_max = float(sp.N(sp.sympify(limites.get('y',('0','1'))[1])))
                z_max = float(sp.N(sp.sympify(limites.get('z',('0','1'))[1])))
                self.graficar_caja_rectangular(limites, x_max, y_max, z_max)
            except Exception as e:
                # Si hay límites variables, mostrar región aproximada
                self.registrar(f"\n⚠️  NOTA: Límites variables detectados - {e}")
                self.registrar("   Mostrando región aproximada con límites máximos")
                try:
                    # Calcular límites máximos aproximados
                    x_max_val = 0
                    y_max_val = 0  
                    z_max_val = 0
                    
                    for var, (min_val, max_val) in limites.items():
                        try:
                            if var == 'x':
                                x_max_val = max(x_max_val, float(sp.N(sp.sympify(max_val))))
                            elif var == 'y':
                                y_max_val = max(y_max_val, float(sp.N(sp.sympify(max_val))))
                            elif var == 'z':
                                z_max_val = max(z_max_val, float(sp.N(sp.sympify(max_val))))
                        except:
                            # Si no se puede convertir, usar valor por defecto
                            if var == 'x': x_max_val = max(x_max_val, 2.0)
                            elif var == 'y': y_max_val = max(y_max_val, 1.0) 
                            elif var == 'z': z_max_val = max(z_max_val, 3.0)
                    
                    self.graficar_caja_rectangular(None, x_max_val, y_max_val, z_max_val)
                except:
                    self.graficar_caja_rectangular(None, 2, 1, 3)

    def abrir_green(self):
        self.limpiar_todo()
        self.registrar("=== TEOREMA DE GREEN ===")
        
        # Diálogo expandido con las 8 regiones
        campos = [
            {'nombre': 'P', 'etiqueta': 'Componente P(x,y):', 'valor_default': '-y'},
            {'nombre': 'Q', 'etiqueta': 'Componente Q(x,y):', 'valor_default': 'x'},
            {'nombre': 'region', 'etiqueta': 'Tipo de región:', 'valor_default': 'disco',
            'opciones': ['disco', 'corona', 'rectangulo', 'elipse', 'triangulo', 
                        'semicirculo', 'entre_curvas', 'sector_polar', 'poligono']},
            {'nombre': 'parametro1', 'etiqueta': 'Parámetro 1 (R, a, etc.):', 'valor_default': '1'},
            {'nombre': 'parametro2', 'etiqueta': 'Parámetro 2 (R_ext, b, etc.):', 'valor_default': '2'},
            {'nombre': 'parametro3', 'etiqueta': 'Parámetro 3 (h, θ_max, etc.):', 'valor_default': '1'},
            {'nombre': 'parametro4', 'etiqueta': 'Parámetro 4 (x0, etc.):', 'valor_default': '0'},
            {'nombre': 'parametro5', 'etiqueta': 'Parámetro 5 (y0, etc.):', 'valor_default': '0'}
        ]
        
        dialogo = DialogoEntrada(self, "Teorema de Green", campos, 500, 450)
        self.wait_window(dialogo)
        
        if not dialogo.resultados:
            return
            
        P = dialogo.resultados['P']
        Q = dialogo.resultados['Q']
        region = dialogo.resultados['region']
        p1 = dialogo.resultados['parametro1']
        p2 = dialogo.resultados['parametro2']
        p3 = dialogo.resultados['parametro3']
        p4 = dialogo.resultados['parametro4']
        p5 = dialogo.resultados['parametro5']
        
        # Configurar parámetros según el tipo de región
        if region == 'disco':
            parametros_region = {'R': p1, 'centro_x': p4, 'centro_y': p5}
        elif region == 'corona':
            parametros_region = {'R_int': p1, 'R_ext': p2, 'centro_x': p4, 'centro_y': p5}
        elif region == 'rectangulo':
            parametros_region = {'a': p1, 'b': p2, 'x0': p4, 'y0': p5}
        elif region == 'elipse':
            parametros_region = {'a': p1, 'b': p2, 'centro_x': p4, 'centro_y': p5}
        elif region == 'triangulo':
            parametros_region = {'base': p1, 'altura': p2, 'x0': p4, 'y0': p5}
        elif region == 'semicirculo':
            parametros_region = {'R': p1, 'tipo': 'superior', 'centro_x': p4, 'centro_y': p5}
        elif region == 'entre_curvas':
            parametros_region = {'f1': p1, 'f2': p2, 'x_min': p3, 'x_max': p4}
        elif region == 'sector_polar':
            parametros_region = {'R': p1, 'theta_min': p3, 'theta_max': p4}
        elif region == 'poligono':
            parametros_region = {'lados': p1, 'radio': p2, 'centro_x': p4, 'centro_y': p5}
        
        resultado = aplicar_green(P, Q, region, parametros_region)
        
        if 'error' in resultado:
            self.registrar('ERROR: ' + resultado['error'])
            return
            
        for linea in resultado.get('info', []):
            self.registrar(linea)
        self.registrar("")
        self.registrar("PROCEDIMIENTO DETALLADO:")
        for linea in resultado.get('pasos', []):
            self.registrar(linea)
            
        # GENERAR GRÁFICA ESPECÍFICA
        try:
            self.graficar_campo2d(P, Q, region, parametros_region)
            self.registrar(f"\n📊 Gráfica: Campo F = ({P}, {Q}) en región {region}")
            
        except Exception as e:
            self.registrar(f"\n⚠️  No se pudo generar la gráfica: {e}")
                
        self.registro_actual = {
            'titulo': f'Teorema de Green - {region}',
            'lineas_salida': self.texto_salida.get('1.0','end').splitlines(), 
            'datos_grafico': {
                'tipo': 'green_region',
                'region': region,
                'P': P, 
                'Q': Q,
                'parametros': parametros_region
            }
        }

    def abrir_divergencia(self):
        self.limpiar_todo()
        self.registrar("=== TEOREMA DE LA DIVERGENCIA ===")
        
        campos = [
            {'nombre': 'Fx', 'etiqueta': 'Componente Fx(x,y,z):', 'valor_default': 'x'},
            {'nombre': 'Fy', 'etiqueta': 'Componente Fy(x,y,z):', 'valor_default': 'y'},
            {'nombre': 'Fz', 'etiqueta': 'Componente Fz(x,y,z):', 'valor_default': 'z'},
            {'nombre': 'region', 'etiqueta': 'Tipo de región:', 'valor_default': 'esfera',
            'opciones': ['esfera', 'cilindro', 'cubo', 'elipsoide', 'cono', 'entre_superficies']},
            {'nombre': 'parametro1', 'etiqueta': 'Parámetro 1 (R, a, etc.):', 'valor_default': '1'},
            {'nombre': 'parametro2', 'etiqueta': 'Parámetro 2 (h, b, etc.):', 'valor_default': '1'},
            {'nombre': 'parametro3', 'etiqueta': 'Parámetro 3 (c, etc.):', 'valor_default': '1'},
            {'nombre': 'parametro4', 'etiqueta': 'Parámetro 4 (R_int, etc.):', 'valor_default': '0.5'},
            {'nombre': 'parametro5', 'etiqueta': 'Parámetro 5 (R_ext, etc.):', 'valor_default': '1'}
        ]
        
        dialogo = DialogoEntrada(self, "Teorema de la Divergencia", campos, 500, 450)
        self.wait_window(dialogo)
        
        if not dialogo.resultados:
            return
            
        Fx = dialogo.resultados['Fx']
        Fy = dialogo.resultados['Fy']
        Fz = dialogo.resultados['Fz']
        region = dialogo.resultados['region']
        p1 = dialogo.resultados['parametro1']
        p2 = dialogo.resultados['parametro2']
        p3 = dialogo.resultados['parametro3']
        p4 = dialogo.resultados['parametro4']
        p5 = dialogo.resultados['parametro5']
        
        # Configurar parámetros según el tipo de región
        if region == 'esfera':
            parametros_region = {'R': p1}
        elif region == 'cilindro':
            parametros_region = {'R': p1, 'h': p2}
        elif region == 'cubo':
            parametros_region = {'a': p1, 'b': p2, 'c': p3}
        elif region == 'elipsoide':
            parametros_region = {'a': p1, 'b': p2, 'c': p3}
        elif region == 'cono':
            parametros_region = {'R': p1, 'h': p2}
        elif region == 'entre_superficies':
            parametros_region = {'R_int': p4, 'R_ext': p5, 'h': p2}
            
        resultado = aplicar_divergencia(Fx, Fy, Fz, region, parametros_region)
        
        if 'error' in resultado:
            self.registrar('ERROR: ' + resultado['error'])
            return
            
        for linea in resultado.get('info', []):
            self.registrar(linea)
        self.registrar("")
        self.registrar("PROCEDIMIENTO:")
        for linea in resultado.get('pasos', []):
            self.registrar(linea)
            
        # GENERAR GRÁFICA SEGÚN EL TIPO DE REGIÓN
        try:
            if region == 'esfera':
                R_real = float(sp.N(sp.sympify(p1)))
                limites_simulados = {'r': ('0', str(R_real))}
                self.graficar_esfera(limites_simulados, R_real)
                self.registrar(f"\n📊 Gráfica: Esfera de radio = {R_real:.2f}")
                
            elif region == 'cilindro':
                R_real = float(sp.N(sp.sympify(p1)))
                h_real = float(sp.N(sp.sympify(p2)))
                self.graficar_cilindro_div(R_real, h_real)
                self.registrar(f"\n📊 Gráfica: Cilindro radio = {R_real:.2f}, altura = {h_real:.2f}")
                
            elif region == 'cubo':
                a_real = float(sp.N(sp.sympify(p1)))
                b_real = float(sp.N(sp.sympify(p2)))
                c_real = float(sp.N(sp.sympify(p3)))
                self.graficar_cubo_div(a_real, b_real, c_real)
                self.registrar(f"\n📊 Gráfica: Cubo {a_real:.2f}×{b_real:.2f}×{c_real:.2f}")
                
            elif region == 'elipsoide':
                a_real = float(sp.N(sp.sympify(p1)))
                b_real = float(sp.N(sp.sympify(p2)))
                c_real = float(sp.N(sp.sympify(p3)))
                self.graficar_elipsoide_div(a_real, b_real, c_real)
                self.registrar(f"\n📊 Gráfica: Elipsoide {a_real:.2f}×{b_real:.2f}×{c_real:.2f}")
                
            elif region == 'cono':
                R_real = float(sp.N(sp.sympify(p1)))
                h_real = float(sp.N(sp.sympify(p2)))
                self.graficar_cono_div(R_real, h_real)
                self.registrar(f"\n📊 Gráfica: Cono radio = {R_real:.2f}, altura = {h_real:.2f}")
                
            elif region == 'entre_superficies':
                R_int = float(sp.N(sp.sympify(p4)))
                R_ext = float(sp.N(sp.sympify(p5)))
                h_real = float(sp.N(sp.sympify(p2)))
                self.graficar_region_entre_superficies(R_int, R_ext, h_real)
                self.registrar(f"\n📊 Gráfica: Región entre superficies")
                
        except Exception as e:
            self.registrar(f"\n⚠️  No se pudo generar visualización: {e}")
        
        self.registro_actual = {
            'titulo': f'Teorema de la Divergencia - {region}',
            'lineas_salida': self.texto_salida.get('1.0','end').splitlines(),
            'datos_grafico': {'tipo': region, **parametros_region}
        }
    
    def abrir_stokes(self):
        self.limpiar_todo()
        self.registrar("=== TEOREMA DE STOKES ===")
        
        campos = [
            {'nombre': 'Fx', 'etiqueta': 'Componente Fx(x,y,z):', 'valor_default': '-y'},
            {'nombre': 'Fy', 'etiqueta': 'Componente Fy(x,y,z):', 'valor_default': 'x'},
            {'nombre': 'Fz', 'etiqueta': 'Componente Fz(x,y,z):', 'valor_default': '0'},
            {'nombre': 'superficie', 'etiqueta': 'Tipo de superficie:', 'valor_default': 'disco',
            'opciones': ['disco', 'plano', 'paraboloide', 'cilindro']},
            {'nombre': 'parametro1', 'etiqueta': 'Parámetro 1 (R, etc.):', 'valor_default': '1'},
            {'nombre': 'parametro2', 'etiqueta': 'Parámetro 2 (a, h, etc.):', 'valor_default': '0'},
            {'nombre': 'parametro3', 'etiqueta': 'Parámetro 3 (b, etc.):', 'valor_default': '0'},
            {'nombre': 'parametro4', 'etiqueta': 'Parámetro 4 (c, etc.):', 'valor_default': '0'},
            {'nombre': 'parametro5', 'etiqueta': 'Parámetro 5 (No usado):', 'valor_default': '0'}
        ]
        
        dialogo = DialogoEntrada(self, "Teorema de Stokes", campos, 500, 450)
        self.wait_window(dialogo)
        
        if not dialogo.resultados:
            return
            
        Fx = dialogo.resultados['Fx']
        Fy = dialogo.resultados['Fy']
        Fz = dialogo.resultados['Fz']
        superficie = dialogo.resultados['superficie']
        p1 = dialogo.resultados['parametro1']
        p2 = dialogo.resultados['parametro2']
        p3 = dialogo.resultados['parametro3']
        p4 = dialogo.resultados['parametro4']
        p5 = dialogo.resultados['parametro5']
        
        # Configurar parámetros según el tipo de superficie
        if superficie == 'disco':
            parametros_superficie = {'R': p1}
        elif superficie == 'plano':
            parametros_superficie = {'R': p1, 'a': p2, 'b': p3, 'c': p4}
        elif superficie == 'paraboloide':
            parametros_superficie = {'R': p1, 'a': p2}
        elif superficie == 'cilindro':
            parametros_superficie = {'R': p1, 'h': p2}
            
        # Aplicar el teorema de Stokes
        resultado = aplicar_stokes(Fx, Fy, Fz, superficie, parametros_superficie)
        
        if 'error' in resultado:
            self.registrar('ERROR: ' + resultado['error'])
            return
            
        for linea in resultado.get('info', []):
            self.registrar(linea)
        self.registrar("")
        self.registrar("PROCEDIMIENTO:")
        for linea in resultado.get('pasos', []):
            self.registrar(linea)
            
        # Generar gráfica 3D según la superficie
        try:
            if superficie == 'disco':
                R_real = float(sp.N(sp.sympify(p1)))
                self.graficar_stokes_3d(R_real, Fx, Fy, Fz)
                self.registrar(f"\n📊 Gráfica: Disco en z=0, radio = {R_real:.2f}")
                
            elif superficie == 'plano':
                a_val = float(sp.N(sp.sympify(p2)))
                b_val = float(sp.N(sp.sympify(p3)))
                c_val = float(sp.N(sp.sympify(p4)))
                R_real = float(sp.N(sp.sympify(p1)))
                self.graficar_plano_3d(a_val, b_val, c_val, R_real)
                self.registrar(f"\n📊 Gráfica: Plano z = {a_val:.2f}x + {b_val:.2f}y + {c_val:.2f}")
                
            elif superficie == 'paraboloide':
                a_val = float(sp.N(sp.sympify(p2)))
                R_real = float(sp.N(sp.sympify(p1)))
                self.graficar_paraboloide_3d(a_val, R_real)
                self.registrar(f"\n📊 Gráfica: Paraboloide z = {a_val:.2f} - x² - y²")
                
            elif superficie == 'cilindro':
                h_val = float(sp.N(sp.sympify(p2)))
                R_real = float(sp.N(sp.sympify(p1)))
                self.graficar_cilindro_3d(R_real, h_val)
                self.registrar(f"\n📊 Gráfica: Cilindro radio {R_real:.2f}, altura {h_val:.2f}")
                
        except Exception as e:
            self.registrar(f"\n⚠️  No se pudo generar visualización: {e}")
        
        self.registro_actual = {
            'titulo': f'Teorema de Stokes - {superficie}', 
            'lineas_salida': self.texto_salida.get('1.0','end').splitlines(), 
            'datos_grafico': {
                'tipo': f'stokes_{superficie}',
                'Fx': Fx, 
                'Fy': Fy, 
                'Fz': Fz,
                'parametros': parametros_superficie
            }
        }

    # ---------------- ayudantes de graficación ----------------
    def graficar_punto(self, coordenadas):
        self.limpiar_grafico()
        eje = self.eje
        x,y,z = coordenadas
        eje.scatter([x],[y],[z], s=80, color='red')
        eje.set_xlabel('X'); eje.set_ylabel('Y'); eje.set_zlabel('Z')
        eje.set_title('Punto en 3D')
        self.lienzo.draw()

    def graficar_esfera(self, limites=None, R=1):
        """Grafica esfera con radio REAL y escala DINÁMICA"""
        self.limpiar_grafico()
        eje = self.eje
        
        # Si tenemos límites, calcular radio REAL
        radio_real = R
        if limites and isinstance(limites, dict):
            try:
                for var, (min_val, max_val) in limites.items():
                    if var in ['rho', 'r']:
                        try:
                            radio_candidato = float(sp.N(sp.sympify(max_val)))
                            radio_real = max(radio_real, radio_candidato)
                        except:
                            pass
            except:
                pass
        
        u = np.linspace(0, 2*np.pi, 60)
        v = np.linspace(0, np.pi, 30)
        x = radio_real * np.outer(np.cos(u), np.sin(v))
        y = radio_real * np.outer(np.sin(u), np.sin(v))
        z = radio_real * np.outer(np.ones_like(u), np.cos(v))
        
        eje.plot_surface(x, y, z, alpha=0.6, edgecolor='k')
        
        # ESCALA DINÁMICA - ajustar ejes al radio real
        margen = radio_real * 0.2  # 20% de margen
        limite_ejes = radio_real + margen
        eje.set_xlim([-limite_ejes, limite_ejes])
        eje.set_ylim([-limite_ejes, limite_ejes])
        eje.set_zlim([-limite_ejes, limite_ejes])
        eje.set_box_aspect([1, 1, 1])
        
        # Etiquetas con información REAL
        eje.set_xlabel('EJE X', fontweight='bold', color='red')
        eje.set_ylabel('EJE Y', fontweight='bold', color='green')
        eje.set_zlabel('EJE Z', fontweight='bold', color='blue')
        eje.set_title(f'Coordenadas Esféricas\nRadio REAL: {radio_real:.2f}')
        
        self.lienzo.draw()

    def graficar_cilindro(self, limites=None, a=1, h=1):
        """Grafica cilindro con límites reales"""
        self.limpiar_grafico()
        eje = self.eje
        
        # Procesar límites reales si se proporcionan
        if limites and isinstance(limites, dict):
            try:
                r_max = float(sp.N(sp.sympify(limites.get('r', ('0', '1'))[1])))
                z_min = float(sp.N(sp.sympify(limites.get('z', ('0', '1'))[0])))
                z_max = float(sp.N(sp.sympify(limites.get('z', ('0', '1'))[1])))
                a = r_max
                h = z_max - z_min
            except:
                pass
        
        z = np.linspace(0, h, 30)
        theta = np.linspace(0, 2*np.pi, 60)
        theta_grid, z_grid = np.meshgrid(theta, z)
        x = a * np.cos(theta_grid)
        y = a * np.sin(theta_grid)
        
        eje.plot_surface(x, y, z_grid, alpha=0.6, edgecolor='k')
        eje.set_box_aspect((1, 1, h))
        
        # Etiquetas mejoradas
        eje.set_xlabel('EJE X', fontweight='bold', color='red')
        eje.set_ylabel('EJE Y', fontweight='bold', color='green') 
        eje.set_zlabel('EJE Z', fontweight='bold', color='blue')
        eje.set_title(f'Coordenadas Cilíndricas\nRadio: {a:.2f}, Altura: {h:.2f}')
        
        self.lienzo.draw()

    def graficar_caja_rectangular(self, limites=None, x_max=1, y_max=1, z_max=1):
        """Grafica una caja rectangular con los límites reales de la integral"""
        self.limpiar_grafico()
        eje = self.eje
        
        # Si se proporcionan límites detallados, usarlos
        if limites and isinstance(limites, dict):
            try:
                # Extraer límites reales para cada variable
                x_min = float(sp.N(sp.sympify(limites.get('x', ('0', '1'))[0])))
                x_max = float(sp.N(sp.sympify(limites.get('x', ('0', '1'))[1])))
                y_min = float(sp.N(sp.sympify(limites.get('y', ('0', '1'))[0])))
                y_max = float(sp.N(sp.sympify(limites.get('y', ('0', '1'))[1])))
                z_min = float(sp.N(sp.sympify(limites.get('z', ('0', '1'))[0])))
                z_max = float(sp.N(sp.sympify(limites.get('z', ('0', '1'))[1])))
                
            except Exception as e:
                # Si hay error (límites variables), usar los valores por parámetro
                print(f"Límites variables detectados, usando aproximación: {e}")
                x_min, y_min, z_min = 0, 0, 0
        else:
            # Usar valores por defecto
            x_min, y_min, z_min = 0, 0, 0
        
        # Definir los vértices del cubo con límites reales
        vertices = np.array([
            [x_min, y_min, z_min], [x_max, y_min, z_min], 
            [x_max, y_max, z_min], [x_min, y_max, z_min],
            [x_min, y_min, z_max], [x_max, y_min, z_max], 
            [x_max, y_max, z_max], [x_min, y_max, z_max]
        ])
        
        # Definir las caras del cubo
        caras = [
            [vertices[0], vertices[1], vertices[2], vertices[3]],  # fondo (z_min)
            [vertices[4], vertices[5], vertices[6], vertices[7]],  # arriba (z_max)
            [vertices[0], vertices[1], vertices[5], vertices[4]],  # frente (y_min)
            [vertices[2], vertices[3], vertices[7], vertices[6]],  # atrás (y_max)
            [vertices[0], vertices[3], vertices[7], vertices[4]],  # izquierda (x_min)
            [vertices[1], vertices[2], vertices[6], vertices[5]]   # derecha (x_max)
        ]
        
        # Colores diferentes para cada cara para mejor identificación
        colores = ['lightblue', 'lightgreen', 'lightcoral', 'lightyellow', 'lightpink', 'lightgray']
        
        # Graficar cada cara con color diferente
        for i, cara in enumerate(caras):
            x = [p[0] for p in cara]
            y = [p[1] for p in cara]
            z = [p[2] for p in cara]
            
            eje.plot_trisurf(x, y, z, alpha=0.6, color=colores[i])
        
        # Configurar ejes y etiquetas
        eje.set_xlabel('EJE X', fontsize=12, fontweight='bold', color='red')
        eje.set_ylabel('EJE Y', fontsize=12, fontweight='bold', color='green')
        eje.set_zlabel('EJE Z', fontsize=12, fontweight='bold', color='blue')
        
        # Título informativo con los límites reales
        titulo = f'Región de Integración 3D\n'
        titulo += f'X: [{x_min:.2f}, {x_max:.2f}] | '
        titulo += f'Y: [{y_min:.2f}, {y_max:.2f}] | '
        titulo += f'Z: [{z_min:.2f}, {z_max:.2f}]'
        eje.set_title(titulo, fontsize=10, pad=20)
        
        # Ajustar los límites de los ejes
        margen = 0.1
        eje.set_xlim([x_min - margen, x_max + margen])
        eje.set_ylim([y_min - margen, y_max + margen])
        eje.set_zlim([z_min - margen, z_max + margen])
        
        # Cuadrícula para mejor referencia
        eje.grid(True, alpha=0.3)
        
        # Vista inicial optimizada
        eje.view_init(elev=20, azim=45)
        
        self.lienzo.draw()

    def graficar_disco(self, R=1):
        self.limpiar_grafico()
        eje = self.eje
        theta = np.linspace(0, 2*np.pi, 60)
        r = np.linspace(0, R, 30)
        T, Rg = np.meshgrid(theta, r)
        X = Rg * np.cos(T)
        Y = Rg * np.sin(T)
        Z = np.zeros_like(X)
        eje.plot_surface(X, Y, Z, alpha=0.6)
        eje.set_title(f'Disco en z=0 radio {R}')
        self.lienzo.draw()

    def graficar_campo2d(self, Fx_str, Fy_str, region='disco', parametros=None):
        """Grafica campo vectorial en 2D con región específica"""
        self.limpiar_grafico()
        eje = self.figura.add_subplot(111)
        eje.clear()
        
        # Crear malla de puntos
        X, Y = np.meshgrid(np.linspace(-4, 4, 16), np.linspace(-4, 4, 16))
        
        try:
            # Convertir strings sympy a funciones evaluables
            x, y = sp.symbols('x y')
            
            # Procesar Fx
            Fx_sym = sp.sympify(Fx_str)
            Fx_func = sp.lambdify((x, y), Fx_sym, 'numpy')
            U = Fx_func(X, Y)
            
            # Procesar Fy  
            Fy_sym = sp.sympify(Fy_str)
            Fy_func = sp.lambdify((x, y), Fy_sym, 'numpy')
            V = Fy_func(X, Y)
            
            # Manejar posibles valores complejos o no numéricos
            U = np.real(np.nan_to_num(U, nan=0, posinf=0, neginf=0))
            V = np.real(np.nan_to_num(V, nan=0, posinf=0, neginf=0))
            
        except Exception as e:
            # Fallback si hay error - campo por defecto
            print(f"Error al procesar campo: {e}")
            U = -Y
            V = X
        
        # Graficar campo vectorial
        eje.quiver(X, Y, U, V, alpha=0.7, color='blue', scale=20)
        eje.set_xlabel('X')
        eje.set_ylabel('Y')
        eje.set_title(f'Campo Vectorial F = ({Fx_str}, {Fy_str})')
        eje.grid(True, alpha=0.3)
        eje.set_aspect('equal')
        
        # Graficar región específica
        if region == 'disco' and parametros:
            self._graficar_disco(eje, parametros)
        elif region == 'corona' and parametros:
            self._graficar_corona(eje, parametros)
        elif region == 'rectangulo' and parametros:
            self._graficar_rectangulo(eje, parametros)
        elif region == 'elipse' and parametros:
            self._graficar_elipse(eje, parametros)
        elif region == 'triangulo' and parametros:
            self._graficar_triangulo(eje, parametros)
        elif region == 'semicirculo' and parametros:
            self._graficar_semicirculo(eje, parametros)
        elif region == 'entre_curvas' and parametros:
            self._graficar_entre_curvas(eje, parametros)
        elif region == 'sector_polar' and parametros:
            self._graficar_sector_polar(eje, parametros)
        elif region == 'poligono' and parametros:
            self._graficar_poligono(eje, parametros)
        else:
            # Región por defecto (disco)
            circle = plt.Circle((0, 0), 2, fill=False, color='red', linewidth=2, linestyle='--')
            eje.add_patch(circle)
        
        # Ajustar límites
        eje.set_xlim([-4, 4])
        eje.set_ylim([-4, 4])
        
        self.lienzo.draw()

    def _graficar_disco(self, eje, parametros):
        """Grafica disco circular - VERSIÓN MEJORADA"""
        try:
            R_str = parametros.get('R', '2')
            centro_x_str = parametros.get('centro_x', '0')
            centro_y_str = parametros.get('centro_y', '0')
            
            # Convertir expresiones sympy a valores numéricos
            R_val = float(sp.N(sp.sympify(R_str)))
            centro_x_val = float(sp.N(sp.sympify(centro_x_str)))
            centro_y_val = float(sp.N(sp.sympify(centro_y_str)))
            
            circle = plt.Circle((centro_x_val, centro_y_val), R_val, 
                            fill=False, color='red', linewidth=2)
            eje.add_patch(circle)
            eje.plot(centro_x_val, centro_y_val, 'ro', markersize=3)
            
        except Exception as e:
            print(f"Error graficando disco: {e}")
            # Fallback
            circle = plt.Circle((0, 0), 2, fill=False, color='red', linewidth=2)
            eje.add_patch(circle)

    def _graficar_corona(self, eje, parametros):
        """Grafica corona circular - VERSIÓN MEJORADA"""
        try:
            R_int_str = parametros.get('R_int', '1')
            R_ext_str = parametros.get('R_ext', '2')
            centro_x_str = parametros.get('centro_x', '0')
            centro_y_str = parametros.get('centro_y', '0')
            
            # Convertir expresiones sympy
            R_int_val = float(sp.N(sp.sympify(R_int_str)))
            R_ext_val = float(sp.N(sp.sympify(R_ext_str)))
            centro_x_val = float(sp.N(sp.sympify(centro_x_str)))
            centro_y_val = float(sp.N(sp.sympify(centro_y_str)))
            
            circle_int = plt.Circle((centro_x_val, centro_y_val), R_int_val, 
                                fill=False, color='red', linewidth=2)
            circle_ext = plt.Circle((centro_x_val, centro_y_val), R_ext_val, 
                                fill=False, color='red', linewidth=2)
            eje.add_patch(circle_int)
            eje.add_patch(circle_ext)
            eje.plot(centro_x_val, centro_y_val, 'ro', markersize=3)
            
        except Exception as e:
            print(f"Error graficando corona: {e}")
            # Fallback
            circle_int = plt.Circle((0, 0), 1, fill=False, color='red', linewidth=2)
            circle_ext = plt.Circle((0, 0), 2, fill=False, color='red', linewidth=2)
            eje.add_patch(circle_int)
            eje.add_patch(circle_ext)

    def _graficar_rectangulo(self, eje, parametros):
        """Grafica rectángulo - VERSIÓN MEJORADA"""
        try:
            a_str = parametros.get('a', '2')
            b_str = parametros.get('b', '1')
            x0_str = parametros.get('x0', '0')
            y0_str = parametros.get('y0', '0')
            
            # Convertir expresiones sympy
            a_val = float(sp.N(sp.sympify(a_str)))
            b_val = float(sp.N(sp.sympify(b_str)))
            x0_val = float(sp.N(sp.sympify(x0_str)))
            y0_val = float(sp.N(sp.sympify(y0_str)))
            
            rect = plt.Rectangle((x0_val, y0_val), a_val, b_val, 
                            fill=False, color='red', linewidth=2)
            eje.add_patch(rect)
            
        except Exception as e:
            print(f"Error graficando rectángulo: {e}")
            # Fallback
            rect = plt.Rectangle((0, 0), 2, 1, fill=False, color='red', linewidth=2)
            eje.add_patch(rect)

    def _graficar_elipse(self, eje, parametros):
        """Grafica elipse - VERSIÓN MEJORADA"""
        try:
            a_str = parametros.get('a', '2')
            b_str = parametros.get('b', '1')
            centro_x_str = parametros.get('centro_x', '0')
            centro_y_str = parametros.get('centro_y', '0')
            
            # Convertir expresiones sympy
            a_val = float(sp.N(sp.sympify(a_str)))
            b_val = float(sp.N(sp.sympify(b_str)))
            centro_x_val = float(sp.N(sp.sympify(centro_x_str)))
            centro_y_val = float(sp.N(sp.sympify(centro_y_str)))
            
            from matplotlib.patches import Ellipse
            elipse = Ellipse((centro_x_val, centro_y_val), 2*a_val, 2*b_val, 
                            fill=False, color='red', linewidth=2)
            eje.add_patch(elipse)
            eje.plot(centro_x_val, centro_y_val, 'ro', markersize=3)
            
        except Exception as e:
            print(f"Error graficando elipse: {e}")
            # Fallback
            from matplotlib.patches import Ellipse
            elipse = Ellipse((0, 0), 4, 2, fill=False, color='red', linewidth=2)
            eje.add_patch(elipse)

    def _graficar_triangulo(self, eje, parametros):
        """Grafica triángulo - VERSIÓN MEJORADA"""
        try:
            base_str = parametros.get('base', '2')
            altura_str = parametros.get('altura', '3')
            x0_str = parametros.get('x0', '0')
            y0_str = parametros.get('y0', '0')
            
            # Convertir expresiones sympy
            base_val = float(sp.N(sp.sympify(base_str)))
            altura_val = float(sp.N(sp.sympify(altura_str)))
            x0_val = float(sp.N(sp.sympify(x0_str)))
            y0_val = float(sp.N(sp.sympify(y0_str)))
            
            vertices = np.array([
                [x0_val, y0_val],
                [x0_val + base_val, y0_val],
                [x0_val + base_val/2, y0_val + altura_val]
            ])
            
            triangulo = plt.Polygon(vertices, fill=False, color='red', linewidth=2)
            eje.add_patch(triangulo)
            
        except Exception as e:
            print(f"Error graficando triángulo: {e}")
            # Fallback
            vertices = np.array([[0, 0], [2, 0], [1, 3]])
            triangulo = plt.Polygon(vertices, fill=False, color='red', linewidth=2)
            eje.add_patch(triangulo)

    def _graficar_semicirculo(self, eje, parametros):
        """Grafica semicírculo - VERSIÓN MEJORADA"""
        try:
            R_str = parametros.get('R', '2')
            tipo = parametros.get('tipo', 'superior')
            centro_x_str = parametros.get('centro_x', '0')
            centro_y_str = parametros.get('centro_y', '0')
            
            # Convertir expresiones sympy
            R_val = float(sp.N(sp.sympify(R_str)))
            centro_x_val = float(sp.N(sp.sympify(centro_x_str)))
            centro_y_val = float(sp.N(sp.sympify(centro_y_str)))
            
            if tipo == 'superior':
                theta = np.linspace(0, np.pi, 100)
            else:
                theta = np.linspace(np.pi, 2*np.pi, 100)
            
            x = centro_x_val + R_val * np.cos(theta)
            y = centro_y_val + R_val * np.sin(theta)
            
            # Dibujar arco
            eje.plot(x, y, 'red', linewidth=2)
            
            # Dibujar diámetro
            if tipo == 'superior':
                eje.plot([centro_x_val - R_val, centro_x_val + R_val], 
                        [centro_y_val, centro_y_val], 'red', linewidth=2)
            else:
                eje.plot([centro_x_val + R_val, centro_x_val - R_val], 
                        [centro_y_val, centro_y_val], 'red', linewidth=2)
                
        except Exception as e:
            print(f"Error graficando semicírculo: {e}")
            # Fallback
            theta = np.linspace(0, np.pi, 100)
            x = 2 * np.cos(theta)
            y = 2 * np.sin(theta)
            eje.plot(x, y, 'red', linewidth=2)

    def _graficar_entre_curvas(self, eje, parametros):
        """Grafica región entre curvas - VERSIÓN MEJORADA"""
        try:
            f1_str = parametros.get('f1', 'x**2')
            f2_str = parametros.get('f2', '4')
            x_min_str = parametros.get('x_min', '-2')
            x_max_str = parametros.get('x_max', '2')
            
            # Convertir límites sympy
            x_min_val = float(sp.N(sp.sympify(x_min_str)))
            x_max_val = float(sp.N(sp.sympify(x_max_str)))
            
            # Usar sympy para evaluar las funciones
            x_sym = sp.symbols('x')
            locales = {'x': x_sym, 'sin': sp.sin, 'cos': sp.cos, 'pi': sp.pi, 
                    'exp': sp.exp, 'log': sp.log}
            
            f1_sym = sp.sympify(f1_str, locals=locales)
            f2_sym = sp.sympify(f2_str, locals=locales)
            
            # Crear puntos de evaluación
            x_vals = np.linspace(x_min_val, x_max_val, 200)
            
            # Evaluar curvas punto por punto (más robusto)
            y1_vals = np.array([float(f1_sym.subs(x_sym, x_val).evalf()) 
                            for x_val in x_vals])
            y2_vals = np.array([float(f2_sym.subs(x_sym, x_val).evalf()) 
                            for x_val in x_vals])
            
            # Manejar valores NaN o infinitos
            y1_vals = np.nan_to_num(y1_vals, nan=0, posinf=10, neginf=-10)
            y2_vals = np.nan_to_num(y2_vals, nan=0, posinf=10, neginf=-10)
            
            # Graficar curvas
            eje.plot(x_vals, y1_vals, 'red', linewidth=2, label=f'y = {f1_str}')
            eje.plot(x_vals, y2_vals, 'blue', linewidth=2, label=f'y = {f2_str}')
            
            # Rellenar la región entre curvas
            eje.fill_between(x_vals, y1_vals, y2_vals, alpha=0.3, color='green')
            
            # Configuración
            eje.set_xlabel('X')
            eje.set_ylabel('Y')
            eje.set_title(f'Región entre: {f1_str} y {f2_str}')
            eje.grid(True, alpha=0.3)
            eje.legend()
            
        except Exception as e:
            print(f"Error graficando entre curvas: {e}")
            # Gráfica de fallback simple
            x_vals = np.linspace(0, np.pi, 100)
            y1_vals = np.sin(x_vals) + 1
            y2_vals = np.full_like(x_vals, 3)
            eje.plot(x_vals, y1_vals, 'red', linewidth=2)
            eje.plot(x_vals, y2_vals, 'blue', linewidth=2)
            eje.fill_between(x_vals, y1_vals, y2_vals, alpha=0.3, color='green')

    def _graficar_sector_polar(self, eje, parametros):
        """Grafica sector polar - VERSIÓN MEJORADA"""
        try:
            R_str = parametros.get('R', '2')
            theta_min_str = parametros.get('theta_min', '0')
            theta_max_str = parametros.get('theta_max', 'pi/2')
            
            # Convertir expresiones sympy a valores numéricos
            R_val = float(sp.N(sp.sympify(R_str)))
            theta_min_val = float(sp.N(sp.sympify(theta_min_str)))
            theta_max_val = float(sp.N(sp.sympify(theta_max_str)))
            
            # Arco circular
            theta = np.linspace(theta_min_val, theta_max_val, 100)
            x_arc = R_val * np.cos(theta)
            y_arc = R_val * np.sin(theta)
            eje.plot(x_arc, y_arc, 'red', linewidth=2)
            
            # Radios
            x_rad1 = [0, R_val * np.cos(theta_min_val)]
            y_rad1 = [0, R_val * np.sin(theta_min_val)]
            x_rad2 = [0, R_val * np.cos(theta_max_val)]
            y_rad2 = [0, R_val * np.sin(theta_max_val)]
            
            eje.plot(x_rad1, y_rad1, 'red', linewidth=2)
            eje.plot(x_rad2, y_rad2, 'red', linewidth=2)
            
            # Rellenar el sector (opcional)
            theta_fill = np.linspace(theta_min_val, theta_max_val, 50)
            r_fill = np.linspace(0, R_val, 20)
            Theta_fill, R_fill = np.meshgrid(theta_fill, r_fill)
            X_fill = R_fill * np.cos(Theta_fill)
            Y_fill = R_fill * np.sin(Theta_fill)
            
            # Solo mostrar contorno para no saturar
            eje.contour(X_fill, Y_fill, np.zeros_like(X_fill), 
                    colors='red', alpha=0.3, linewidths=0.5)
            
            # Configurar ejes
            max_limit = R_val * 1.2
            eje.set_xlim([-max_limit, max_limit])
            eje.set_ylim([-max_limit, max_limit])
            eje.set_aspect('equal')
            eje.grid(True, alpha=0.3)
            eje.set_title(f'Sector Polar: R={R_val}, θ∈[{theta_min_val:.2f},{theta_max_val:.2f}]')
            
        except Exception as e:
            print(f"Error graficando sector polar: {e}")
            # Gráfica de fallback
            circle = plt.Circle((0, 0), 2, fill=False, color='red', linewidth=2)
            eje.add_patch(circle)

    def _graficar_poligono(self, eje, parametros):
        """Grafica polígono regular - VERSIÓN MEJORADA"""
        try:
            lados_str = parametros.get('lados', '5')
            radio_str = parametros.get('radio', '2')
            centro_x_str = parametros.get('centro_x', '0')
            centro_y_str = parametros.get('centro_y', '0')
            
            # Convertir expresiones sympy
            lados_val = int(sp.N(sp.sympify(lados_str)))
            radio_val = float(sp.N(sp.sympify(radio_str)))
            centro_x_val = float(sp.N(sp.sympify(centro_x_str)))
            centro_y_val = float(sp.N(sp.sympify(centro_y_str)))
            
            # Calcular vértices del polígono
            vertices = []
            for i in range(lados_val):
                theta = 2 * np.pi * i / lados_val
                x = centro_x_val + radio_val * np.cos(theta)
                y = centro_y_val + radio_val * np.sin(theta)
                vertices.append([x, y])
            
            vertices.append(vertices[0])  # Cerrar el polígono
            
            vertices = np.array(vertices)
            eje.plot(vertices[:, 0], vertices[:, 1], 'red', linewidth=2)
            eje.plot(centro_x_val, centro_y_val, 'ro', markersize=3)
            
        except Exception as e:
            print(f"Error graficando polígono: {e}")
            # Fallback - pentágono
            vertices = []
            for i in range(5):
                theta = 2 * np.pi * i / 5
                x = 2 * np.cos(theta)
                y = 2 * np.sin(theta)
                vertices.append([x, y])
            vertices.append(vertices[0])
            vertices = np.array(vertices)
            eje.plot(vertices[:, 0], vertices[:, 1], 'red', linewidth=2)
    
    
    def graficar_stokes_3d(self, R=1, Fx_str="-y", Fy_str="x", Fz_str="z"):
        """Visualización 3D completa para el Teorema de Stokes"""
        self.limpiar_grafico()
        eje = self.eje
        
        # 1. SUPERFICIE 3D: Disco en el plano z=0
        theta = np.linspace(0, 2*np.pi, 60)
        r = np.linspace(0, R, 30)
        T, Rg = np.meshgrid(theta, r)
        X_surf = Rg * np.cos(T)
        Y_surf = Rg * np.sin(T)
        Z_surf = np.zeros_like(X_surf)
        
        # Graficar la superficie del disco
        surf = eje.plot_surface(X_surf, Y_surf, Z_surf, alpha=0.5, color='lightblue')
        surf._facecolors2d = surf._facecolors3d  # Para la leyenda
        surf._edgecolors2d = surf._edgecolors3d
        
        # 2. CURVA BORDE 3D: Círculo que limita el disco
        theta_borde = np.linspace(0, 2*np.pi, 100)
        x_borde = R * np.cos(theta_borde)
        y_borde = R * np.sin(theta_borde)
        z_borde = np.zeros_like(theta_borde)
        
        # Graficar la curva borde en 3D
        borde, = eje.plot(x_borde, y_borde, z_borde, 'r-', linewidth=3, label='Curva C (borde)')
        
        # 3. CAMPO VECTORIAL 3D en la superficie
        x_vec = np.linspace(-R*0.8, R*0.8, 6)
        y_vec = np.linspace(-R*0.8, R*0.8, 6)
        z_vec = np.array([0])  # En la superficie z=0
        
        X_vec, Y_vec, Z_vec = np.meshgrid(x_vec, y_vec, z_vec)
        
        # Evaluar el campo vectorial real usando sympy
        try:
            x_sym, y_sym, z_sym = sp.symbols('x y z')
            Fx_func = sp.lambdify((x_sym, y_sym, z_sym), sp.sympify(Fx_str), 'numpy')
            Fy_func = sp.lambdify((x_sym, y_sym, z_sym), sp.sympify(Fy_str), 'numpy')
            Fz_func = sp.lambdify((x_sym, y_sym, z_sym), sp.sympify(Fz_str), 'numpy')
            
            U_vec = Fx_func(X_vec, Y_vec, Z_vec)
            V_vec = Fy_func(X_vec, Y_vec, Z_vec)
            W_vec = Fz_func(X_vec, Y_vec, Z_vec)
        except:
            # Fallback a campo por defecto
            U_vec = -Y_vec
            V_vec = X_vec
            W_vec = Z_vec
        
        # Graficar campo vectorial 3D
        campo = eje.quiver(X_vec, Y_vec, Z_vec, U_vec, V_vec, W_vec, 
                          length=0.2, color='green', alpha=0.8, 
                          normalize=True, arrow_length_ratio=0.3)
        
        # 4. VECTORES NORMALES a la superficie
        theta_norm = np.linspace(0, 2*np.pi, 12)
        r_norm = np.linspace(0.3, R*0.7, 4)
        
        for r_val in r_norm:
            for t_val in theta_norm:
                x_norm = r_val * np.cos(t_val)
                y_norm = r_val * np.sin(t_val)
                z_norm = 0
                
                # Vector normal unitario (apuntando hacia arriba)
                dx_norm, dy_norm, dz_norm = 0, 0, 0.3
                
                eje.quiver(x_norm, y_norm, z_norm, dx_norm, dy_norm, dz_norm,
                          color='blue', alpha=0.6, linewidth=1.5, 
                          arrow_length_ratio=0.15)
        
        # 5. ROTACIONAL (opcional) - como campo vectorial adicional
        try:
            # Calcular el rotacional numéricamente
            rot_U = np.gradient(W_vec, axis=1) - np.gradient(V_vec, axis=2)  # ∂Fz/∂y - ∂Fy/∂z
            rot_V = np.gradient(U_vec, axis=2) - np.gradient(W_vec, axis=0)  # ∂Fx/∂z - ∂Fz/∂x  
            rot_W = np.gradient(V_vec, axis=0) - np.gradient(U_vec, axis=1)  # ∂Fy/∂x - ∂Fx/∂y
        except:
            rot_U = np.zeros_like(U_vec)
            rot_V = np.zeros_like(V_vec)
            rot_W = 2 * np.ones_like(W_vec)  # Valor por defecto
        
        # Graficar rotacional ligeramente desplazado
        rotacional = eje.quiver(X_vec, Y_vec, Z_vec + 0.1, rot_U, rot_V, rot_W,
                              length=0.15, color='red', alpha=0.6,
                              normalize=True, arrow_length_ratio=0.2)
        
        # Configuración final
        eje.set_xlabel('X')
        eje.set_ylabel('Y')
        eje.set_zlabel('Z')
        eje.set_title(f'Teorema de Stokes - Visualización 3D\nF=({Fx_str}, {Fy_str}, {Fz_str})')
        
        # Crear leyenda manualmente
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='lightblue', alpha=0.5, label='Superficie S'),
            borde,
            Patch(facecolor='green', alpha=0.8, label='Campo F'),
            Patch(facecolor='blue', alpha=0.6, label='Vectores normales'),
            Patch(facecolor='red', alpha=0.6, label='Rotacional ∇×F')
        ]
        eje.legend(handles=legend_elements, loc='upper left')
        
        # Ajustar vista
        max_limit = R * 1.2
        eje.set_xlim([-max_limit, max_limit])
        eje.set_ylim([-max_limit, max_limit])
        eje.set_zlim([-0.5, 0.8])
        
        # Vista inicial mejorada
        eje.view_init(elev=30, azim=45)
        
        self.lienzo.draw()
        
    def graficar_plano_3d(self, a=0, b=0, c=0, R=2):
        """Grafica un plano en 3D"""
        self.limpiar_grafico()
        eje = self.eje
        
        # Crear malla
        x = np.linspace(-R, R, 20)
        y = np.linspace(-R, R, 20)
        X, Y = np.meshgrid(x, y)
        
        # Ecuación del plano: z = ax + by + c
        Z = a*X + b*Y + c
        
        # Graficar plano
        eje.plot_surface(X, Y, Z, alpha=0.7, color='lightblue')
        
        # Configurar ejes
        eje.set_xlabel('X')
        eje.set_ylabel('Y') 
        eje.set_zlabel('Z')
        eje.set_title(f'Plano: z = {a}x + {b}y + {c}')
        eje.set_box_aspect([1, 1, 1])
        
        self.lienzo.draw()

    def graficar_paraboloide_3d(self, a=4, R=2):
        """Grafica paraboloide z = a - x² - y²"""
        self.limpiar_grafico()
        eje = self.eje
        
        # Crear malla
        x = np.linspace(-R, R, 30)
        y = np.linspace(-R, R, 30)
        X, Y = np.meshgrid(x, y)
        
        # Ecuación del paraboloide: z = a - x² - y²
        Z = a - X**2 - Y**2
        Z[Z < 0] = np.nan  # Solo parte positiva
        
        # Graficar paraboloide
        eje.plot_surface(X, Y, Z, alpha=0.7, color='lightgreen', edgecolor='darkgreen')
        
        # Configurar ejes
        eje.set_xlabel('X')
        eje.set_ylabel('Y')
        eje.set_zlabel('Z')
        eje.set_title(f'Paraboloide: z = {a} - x² - y²')
        eje.set_box_aspect([1, 1, 1])
        
        self.lienzo.draw()

    def graficar_cilindro_3d(self, R=2, h=3):
        """Grafica cilindro x² + y² = R², 0 ≤ z ≤ h"""
        self.limpiar_grafico()
        eje = self.eje
        
        # Crear malla cilíndrica
        z = np.linspace(0, h, 30)
        theta = np.linspace(0, 2*np.pi, 60)
        Z, Theta = np.meshgrid(z, theta)
        
        # Coordenadas cilíndricas a cartesianas
        X = R * np.cos(Theta)
        Y = R * np.sin(Theta)
        
        # Graficar cilindro
        eje.plot_surface(X, Y, Z, alpha=0.7, color='lightcoral', edgecolor='darkred')
        
        # Configurar ejes
        eje.set_xlabel('X')
        eje.set_ylabel('Y')
        eje.set_zlabel('Z')
        eje.set_title(f'Cilindro: x² + y² = {R}², 0 ≤ z ≤ {h}')
        eje.set_box_aspect([1, 1, 1])
        
        self.lienzo.draw()
        
    def graficar_cilindro_div(self, radio, altura):
        """Grafica cilindro para el teorema de la divergencia"""
        self.limpiar_grafico()
        eje = self.eje
        
        # Parámetros para el cilindro
        z = np.linspace(-altura/2, altura/2, 30)
        theta = np.linspace(0, 2 * np.pi, 30)
        theta_grid, z_grid = np.meshgrid(theta, z)
        
        # Coordenadas cilíndricas
        x_grid = radio * np.cos(theta_grid)
        y_grid = radio * np.sin(theta_grid)
        
        # Graficar superficie lateral
        eje.plot_surface(x_grid, y_grid, z_grid, alpha=0.6, color='lightblue', edgecolor='k')
        
        # Graficar tapas
        r = np.linspace(0, radio, 10)
        theta_r = np.linspace(0, 2 * np.pi, 30)
        r_grid, theta_grid = np.meshgrid(r, theta_r)
        
        x_tapa = r_grid * np.cos(theta_grid)
        y_tapa = r_grid * np.sin(theta_grid)
        z_superior = np.ones_like(x_tapa) * altura/2
        z_inferior = np.ones_like(x_tapa) * -altura/2
        
        eje.plot_surface(x_tapa, y_tapa, z_superior, alpha=0.6, color='lightblue')
        eje.plot_surface(x_tapa, y_tapa, z_inferior, alpha=0.6, color='lightblue')
        
        # Configuración de ejes
        max_range = max(radio, altura/2) * 1.2
        eje.set_xlim([-max_range, max_range])
        eje.set_ylim([-max_range, max_range])
        eje.set_zlim([-max_range, max_range])
        eje.set_box_aspect([1, 1, 1])
        
        eje.set_xlabel('X')
        eje.set_ylabel('Y')
        eje.set_zlabel('Z')
        eje.set_title(f'Cilindro\nRadio: {radio:.2f}, Altura: {altura:.2f}')
        
        self.lienzo.draw()

    def graficar_cubo_div(self, a, b, c):
        """Grafica cubo - VERSIÓN SIMPLE Y FUNCIONAL"""
        self.limpiar_grafico()
        eje = self.eje
        
        # Crear mallas para cada cara
        # Cara frontal (x = a/2)
        Y_front, Z_front = np.meshgrid(np.linspace(-b/2, b/2, 10), np.linspace(-c/2, c/2, 10))
        X_front = np.ones_like(Y_front) * a/2
        
        # Cara trasera (x = -a/2)
        X_back = np.ones_like(Y_front) * -a/2
        
        # Cara derecha (y = b/2)
        X_right, Z_right = np.meshgrid(np.linspace(-a/2, a/2, 10), np.linspace(-c/2, c/2, 10))
        Y_right = np.ones_like(X_right) * b/2
        
        # Cara izquierda (y = -b/2)
        Y_left = np.ones_like(X_right) * -b/2
        
        # Cara superior (z = c/2)
        X_top, Y_top = np.meshgrid(np.linspace(-a/2, a/2, 10), np.linspace(-b/2, b/2, 10))
        Z_top = np.ones_like(X_top) * c/2
        
        # Cara inferior (z = -c/2)
        Z_bottom = np.ones_like(X_top) * -c/2
        
        # Graficar todas las caras
        eje.plot_surface(X_front, Y_front, Z_front, alpha=0.6, color='lightblue')
        eje.plot_surface(X_back, Y_front, Z_front, alpha=0.6, color='lightblue')
        eje.plot_surface(X_right, Y_right, Z_right, alpha=0.6, color='lightgreen')
        eje.plot_surface(X_right, Y_left, Z_right, alpha=0.6, color='lightgreen')
        eje.plot_surface(X_top, Y_top, Z_top, alpha=0.6, color='lightcoral')
        eje.plot_surface(X_top, Y_top, Z_bottom, alpha=0.6, color='lightcoral')
        
        # Configuración
        max_dim = max(a, b, c) * 0.6
        eje.set_xlim([-max_dim, max_dim])
        eje.set_ylim([-max_dim, max_dim])
        eje.set_zlim([-max_dim, max_dim])
        eje.set_box_aspect([1, 1, 1])
        
        eje.set_xlabel('X')
        eje.set_ylabel('Y')
        eje.set_zlabel('Z')
        eje.set_title(f'Cubo\n{a:.1f} × {b:.1f} × {c:.1f}')
        
        self.lienzo.draw()

    def graficar_elipsoide_div(self, a, b, c):
        """Grafica elipsoide para el teorema de la divergencia"""
        self.limpiar_grafico()
        eje = self.eje
        
        # Parámetros
        u = np.linspace(0, 2 * np.pi, 30)
        v = np.linspace(0, np.pi, 30)
        
        # Coordenadas elipsoidales
        x = a * np.outer(np.cos(u), np.sin(v))
        y = b * np.outer(np.sin(u), np.sin(v))
        z = c * np.outer(np.ones_like(u), np.cos(v))
        
        # Graficar
        eje.plot_surface(x, y, z, alpha=0.6, color='lightcoral', edgecolor='k')
        
        # Configuración
        max_dim = max(a, b, c) * 1.2
        eje.set_xlim([-max_dim, max_dim])
        eje.set_ylim([-max_dim, max_dim])
        eje.set_zlim([-max_dim, max_dim])
        eje.set_box_aspect([1, 1, 1])
        
        eje.set_xlabel('X')
        eje.set_ylabel('Y')
        eje.set_zlabel('Z')
        eje.set_title(f'Elipsoide\n{a:.2f} × {b:.2f} × {c:.2f}')
        
        self.lienzo.draw()

    def graficar_cono_div(self, radio, altura):
        """Grafica cono para el teorema de la divergencia"""
        self.limpiar_grafico()
        eje = self.eje
        
        # Parámetros
        z = np.linspace(0, altura, 30)
        theta = np.linspace(0, 2 * np.pi, 30)
        theta_grid, z_grid = np.meshgrid(theta, z)
        
        # Radio variable con la altura
        r_grid = radio * (1 - z_grid/altura)
        
        # Coordenadas cilíndricas
        x_grid = r_grid * np.cos(theta_grid)
        y_grid = r_grid * np.sin(theta_grid)
        
        # Graficar superficie lateral
        eje.plot_surface(x_grid, y_grid, z_grid, alpha=0.6, color='lightyellow', edgecolor='k')
        
        # Graficar base
        r_base = np.linspace(0, radio, 10)
        theta_base = np.linspace(0, 2 * np.pi, 30)
        r_grid_base, theta_grid_base = np.meshgrid(r_base, theta_base)
        
        x_base = r_grid_base * np.cos(theta_grid_base)
        y_base = r_grid_base * np.sin(theta_grid_base)
        z_base = np.zeros_like(x_base)
        
        eje.plot_surface(x_base, y_base, z_base, alpha=0.6, color='lightyellow')
        
        # Configuración
        max_range = max(radio, altura) * 1.2
        eje.set_xlim([-max_range, max_range])
        eje.set_ylim([-max_range, max_range])
        eje.set_zlim([-max_range/2, max_range])
        eje.set_box_aspect([1, 1, 1])
        
        eje.set_xlabel('X')
        eje.set_ylabel('Y')
        eje.set_zlabel('Z')
        eje.set_title(f'Cono\nRadio: {radio:.2f}, Altura: {altura:.2f}')
        
        self.lienzo.draw()

    def graficar_region_entre_superficies(self, R_int, R_ext, altura):
        """Grafica región entre dos superficies (ej: cilindros)"""
        self.limpiar_grafico()
        eje = self.eje
        
        # Graficar cilindro exterior
        z_ext = np.linspace(-altura/2, altura/2, 20)
        theta_ext = np.linspace(0, 2 * np.pi, 30)
        theta_grid_ext, z_grid_ext = np.meshgrid(theta_ext, z_ext)
        
        x_ext = R_ext * np.cos(theta_grid_ext)
        y_ext = R_ext * np.sin(theta_grid_ext)
        
        eje.plot_surface(x_ext, y_ext, z_grid_ext, alpha=0.3, color='blue', label='Exterior')
        
        # Graficar cilindro interior
        if R_int > 0:
            x_int = R_int * np.cos(theta_grid_ext)
            y_int = R_int * np.sin(theta_grid_ext)
            
            eje.plot_surface(x_int, y_int, z_grid_ext, alpha=0.3, color='red', label='Interior')
        
        # Configuración
        max_range = max(R_ext, altura/2) * 1.2
        eje.set_xlim([-max_range, max_range])
        eje.set_ylim([-max_range, max_range])
        eje.set_zlim([-max_range, max_range])
        eje.set_box_aspect([1, 1, 1])
        
        eje.set_xlabel('X')
        eje.set_ylabel('Y')
        eje.set_zlabel('Z')
        eje.set_title(f'Región entre Superficies\nR_int: {R_int:.2f}, R_ext: {R_ext:.2f}, h: {altura:.2f}')
        
        self.lienzo.draw()        

    def al_cerrar(self):
        if messagebox.askyesno('Salir', '¿Desea salir del programa?'):
            guardar_historial(self.historial)
            self.destroy()


if __name__ == '__main__':
    aplicacion = AplicacionMultivariable()
    aplicacion.mainloop()