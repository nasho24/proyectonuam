// Cálculos para factores tributarios
class CalculadoraFactores {
    constructor() {
        this.factores = {};
    }

    // Validar que la suma de factores 8-16 sea <= 1
    validarSumaFactores() {
        const factores = [8, 9, 10, 11, 12, 13, 14, 15, 16];
        let suma = 0;
        
        factores.forEach(num => {
            const valor = parseFloat(this.factores[`factor_${num}`]) || 0;
            suma += valor;
        });

        return {
            valido: suma <= 1,
            suma: suma,
            mensaje: suma <= 1 ? '✅ Suma válida' : '❌ La suma no puede ser mayor a 1'
        };
    }

    // Calcular factores desde montos
    calcularDesdeMontos(montos) {
        const total = Object.values(montos).reduce((sum, monto) => sum + (parseFloat(monto) || 0), 0);
        
        if (total === 0) return {};
        
        const factores = {};
        for (let i = 8; i <= 37; i++) {
            const monto = parseFloat(montos[`monto_${i}`]) || 0;
            factores[`factor_${i}`] = total > 0 ? (monto / total).toFixed(8) : 0;
        }
        
        this.factores = factores;
        return factores;
    }
}

// Inicializar calculadora
const calculadora = new CalculadoraFactores();