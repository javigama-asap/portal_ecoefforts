(function() {
    'use strict';

    const iniciarMonitor = ($) => {
        console.log("EcoEfforts: Vigilancia de líneas activa (Conceptos + Cantidades)");

        // Diccionarios para recordar los valores y no saturar el servidor
        const ultimosConceptos = {};
        const ultimasCantidades = {};

        const procesarCambios = () => {
            // 1. VIGILAR CONCEPTOS (Para traer el precio base)
            $('select[id$="-concepto"]').each(function() {
                const $select = $(this);
                const idSelect = $select.attr('id');
                const valorConcepto = $select.val();
                const filaId = idSelect.split('-')[1];
                const $campoPrecio = $(`#id_lineas-${filaId}-precio`);

                if (valorConcepto && valorConcepto !== ultimosConceptos[idSelect]) {
                    ultimosConceptos[idSelect] = valorConcepto;
                    
                    $.ajax({
                        url: '/admin/obtener-precio-ajax/',
                        data: { 'tipo': 'Concepto', 'id': valorConcepto },
                        success: function(data) {
                            // Guardamos el precio unitario en un atributo HTML para que persista
                            $campoPrecio.attr('data-unitario', data.precio);
                            // Forzamos el recalculo inmediato
                            const cant = parseInt($(`#id_lineas-${filaId}-cantidad`).val()) || 0;
                            $campoPrecio.val((data.precio * cant).toFixed(2));
                            console.log("Nuevo precio base para fila " + filaId + ": " + data.precio);
                        }
                    });
                }
            });

            // 2. VIGILAR CANTIDADES (Para multiplicar localmente)
            $('input[id$="-cantidad"]').each(function() {
                const $inputCant = $(this);
                const idCant = $inputCant.attr('id');
                const valorCant = parseInt($inputCant.val()) || 0;
                const filaId = idCant.split('-')[1];
                const $campoPrecio = $(`#id_lineas-${filaId}-precio`);

                if (valorCant !== ultimasCantidades[idCant]) {
                    ultimasCantidades[idCant] = valorCant;
                    
                    const precioUnitario = parseFloat($campoPrecio.attr('data-unitario')) || 0;
                    if (precioUnitario > 0) {
                        $campoPrecio.val((precioUnitario * valorCant).toFixed(2));
                    }
                }
            });
        };

        // Escaneamos la página cada 500ms
        setInterval(procesarCambios, 500);
    };

    // Bucle para esperar a jQuery de Django
    const esperarJquery = setInterval(function() {
        const $ = window.django ? django.jQuery : window.jQuery;
        if ($) {
            clearInterval(esperarJquery);
            iniciarMonitor($);
        }
    }, 100);

})();