(function() {
    'use strict';

    const camposFact = [
        'id_email_facturacion', 'id_direccion_facturacion', 'id_numero_facturacion', 
        'id_localidad_facturacion', 'id_cp_facturacion', 'id_provincia_facturacion', 
        'id_observaciones_facturacion'
    ];

    function actualizarInterfaz() {
        const checkbox = document.getElementById('id_mismos_datos');
        if (!checkbox) return;

        const esMismo = checkbox.checked;

        camposFact.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                const contenedor = el.closest('.form-group');
                if (contenedor) {
                    contenedor.style.display = esMismo ? 'none' : 'block';
                }
            }
        });

        if (esMismo) sincronizarDatos();
    }

    function sincronizarDatos() {
        const fiscales = ['id_email_fiscal', 'id_direccion_fiscal', 'id_numero_fiscal', 'id_localidad_fiscal', 'id_cp_fiscal', 'id_provincia_fiscal', 'id_observaciones_fiscal'];
        
        fiscales.forEach((idFis, index) => {
            const origen = document.getElementById(idFis);
            const destino = document.getElementById(camposFact[index]);
            // Solo copiamos si el destino es diferente para evitar bucles lógicos
            if (origen && destino && origen.value !== destino.value) {
                destino.value = origen.value;
                if (idFis.includes('provincia') && window.jQuery) {
                    window.jQuery(destino).trigger('change');
                }
            }
        });
    }

    // Usamos delegación de eventos para no sobrecargar
    document.addEventListener('change', (e) => {
        if (e.target.id === 'id_mismos_datos') {
            actualizarInterfaz();
        }
    });

    document.addEventListener('input', (e) => {
        // Solo sincronizamos si el cambio viene de un campo fiscal
        if (e.target.id.includes('_fiscal')) {
            const checkbox = document.getElementById('id_mismos_datos');
            if (checkbox && checkbox.checked) {
                sincronizarDatos();
            }
        }
    });

    // En lugar de un Observer constante, ejecutamos solo al cargar 
    // y cuando el usuario hace clic en las pestañas de Jazzmin
    window.addEventListener('load', actualizarInterfaz);
    
    document.addEventListener('click', (e) => {
        if (e.target.closest('.nav-tabs')) {
            setTimeout(actualizarInterfaz, 100);
        }
    });

})();