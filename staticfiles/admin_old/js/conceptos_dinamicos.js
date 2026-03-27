(function() {
    'use strict';

    const ejecutarLogica = ($) => {
        const refrescar = () => {
            const valor = $('select[id$="tipo_concepto"]').val();
            const esExtra = $('input[id$="info_adicional"]').is(':checked');

            $('.field-envase').toggle(valor === 'Envase');
            $('.field-residuo').toggle(valor === 'Residuo');
            
            const adicionales = $('.field-descripcion_adicional, .field-cantidad_adicional, .field-precio_adicional');
            esExtra ? adicionales.show() : adicionales.hide();
        };

        // 1. EL OBSERVADOR: Vigilamos cambios en el árbol HTML
        const observer = new MutationObserver((mutations) => {
            // Si algo cambia en el DOM de los contenedores de Select2, refrescamos
            refrescar();
        });

        // Buscamos el contenedor visual que Jazzmin crea para el Select2
        const contenedorSelect2 = document.querySelector('select[id$="tipo_concepto"] + .select2');
        
        if (contenedorSelect2) {
            observer.observe(contenedorSelect2, {
                childList: true, 
                subtree: true, 
                characterData: true 
            });
        }

        // 2. Evento para el checkbox (este sí es un input real y no falla)
        $(document).on('change', 'input[id$="info_adicional"]', refrescar);

        // Ejecución inicial
        refrescar();
    };

    const actualizarPrecio = () => {
        const valorTipo = $('#id_tipo_concepto').val();
        const idSeleccionado = (valorTipo === 'Envase' ? $('#id_envase').val() : $('#id_residuo').val());
        const cantidad = parseFloat($('#id_cantidad_base_incluida').val()) || 0;

        if (idSeleccionado && (valorTipo === 'Envase' || valorTipo === 'Residuo')) {
            // Llamada AJAX
            $.ajax({
                url: '/admin/obtener-precio-ajax/',
                data: {
                    'tipo': valorTipo,
                    'id': idSeleccionado
                },
                success: function(data) {
                    const total = (data.precio * cantidad).toFixed(2);
                    $('#id_precio_base').val(total);
                    console.log("Precio actualizado por AJAX:", total);
                }
            });
        }
    };

    $(document).ready(function() {
        // Escuchar cambios en tipo, selectores y cantidad
        $(document).on('change', '#id_tipo_concepto, #id_envase, #id_residuo', actualizarPrecio);
        $(document).on('input', '#id_cantidad_base_incluida', actualizarPrecio);
    });

    window.addEventListener('load', function() {
        const $ = window.django ? django.jQuery : window.jQuery;
        if ($) ejecutarLogica($);
    });
})();