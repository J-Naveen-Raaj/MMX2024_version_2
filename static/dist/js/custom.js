$(function () {
    "use strict";
    $(function () {
        $(".preloader").fadeOut();
    });
   
    // ==============================================================
    // This is for the top header part and sidebar part
    // ==============================================================
    var set = function () {
        var width = (window.innerWidth > 0) ? window.innerWidth : this.screen.width;
        var topOffset = 190;
        if (width < 1170) {
            $("body").addClass("mini-sidebar");
            // $('.navbar-brand span').hide();
            $(".sidebartoggler i").addClass("ti-menu");
        }
        else {
            $("body").removeClass("mini-sidebar");
            // $('.navbar-brand span').show();
       }
         var height = ((window.innerHeight > 0) ? window.innerHeight : this.screen.height) - 1;
        height = height - topOffset;
        if (height < 1) height = 1;
        if (height > topOffset) {
            $(".page-wrapper").css("min-height", (height) + "px");
        }
    };
    $(window).ready(set);
    $(window).on("resize", set);
    // ==============================================================
    // Theme options
    // ==============================================================
    $(".sidebartoggler").on('click', function () {
        if ($("body").hasClass("mini-sidebar")) {
            $("body").trigger("resize");
            $("body").removeClass("mini-sidebar");
            $('.navbar-brand span').show();
        }
        else {
            $("body").trigger("resize");
            $("body").addClass("mini-sidebar");
            $('.navbar-brand span').hide();
        }
    });
    // this is for close icon when navigation open in mobile view
    $(".nav-toggler").click(function () {
        $("body").toggleClass("show-sidebar");
        $(".nav-toggler i").toggleClass("ti-menu");
        $(".nav-toggler i").addClass("ti-close");
    });
    $(".search-box a, .search-box .app-search .srh-btn").on('click', function () {
        $(".app-search").toggle(200);
    });
    // ==============================================================
    // Right sidebar options
    // ==============================================================
    $(".right-side-toggle").click(function () {
        $(".right-sidebar").slideDown(50);
        $(".right-sidebar").toggleClass("shw-rside");
    });
    // ==============================================================
    // This is for the floating labels
    // ==============================================================
    $('.floating-labels .form-control').on('focus blur', function (e) {
        $(this).parents('.form-group').toggleClass('focused', (e.type === 'focus' || this.value.length > 0));
    }).trigger('blur');

    // ==============================================================
    //tooltip
    // ==============================================================
    $(function () {
            $('[data-toggle="tooltip"]').tooltip()
        })
    // ==============================================================
    //Popover
    // ==============================================================
    $(function () {
         $('[data-toggle="popover"]').popover()
    })

    // ==============================================================
    // Perfact scrollbar
    // ==============================================================
    $('.right-side-panel, .message-center, .right-sidebar').perfectScrollbar();
    // ==============================================================
    // Resize all elements
    // ==============================================================
    $("body").trigger("resize");
    // ==============================================================
    // To do list
    // ==============================================================
    $(".list-task li label").click(function () {
        $(this).toggleClass("task-done");
    });
    // ==============================================================
    // Collapsable cards
    // ==============================================================
    $('a[data-action="collapse"]').on('click', function (e) {
        e.preventDefault();
        $(this).closest('.card').find('[data-action="collapse"] i').toggleClass('ti-minus ti-plus');
        $(this).closest('.card').children('.card-body').collapse('toggle');
    });
    // Toggle fullscreen
    $('a[data-action="expand"]').on('click', function (e) {
        e.preventDefault();
        $(this).closest('.card').find('[data-action="expand"] i').toggleClass('mdi-arrow-expand mdi-arrow-compress');
        $(this).closest('.card').toggleClass('card-fullscreen');
    });
    // Close Card
    $('a[data-action="close"]').on('click', function () {
        $(this).closest('.card').removeClass().slideUp('fast');
    });
    // ==============================================================
    // fixed navigattion while scrolll
    // ==============================================================
    function collapseNavbar() {
        if ($(window).scrollTop() > 80) {
            $("body").addClass("fixed-sidebar");
            $(".left-sidebar").addClass("animated slideInDown");

        } else {
            $("body").removeClass("fixed-sidebar");
            $(".left-sidebar").removeClass("animated slideInDown");
        }
    }
    $(window).scroll(collapseNavbar);
    collapseNavbar()
    // ==============================================================
    // Color variation
    // ==============================================================

    var mySkins = [
        "skin-default",
        "skin-green",
        "skin-red",
        "skin-blue",
        "skin-purple",
        "skin-megna",
        "skin-default-dark",
        "skin-green-dark",
        "skin-red-dark",
        "skin-blue-dark",
        "skin-purple-dark",
        "skin-megna-dark"
    ]
        /**
         * Get a prestored setting
         *
         * @param String name Name of of the setting
         * @returns String The value of the setting | null
         */
    function get(name) {
        if (typeof (Storage) !== 'undefined') {
            return localStorage.getItem(name)
        }
        else {
            window.alert('Please use a modern browser to properly view this template!')
        }
    }
    /**
     * Store a new settings in the browser
     *
     * @param String name Name of the setting
     * @param String val Value of the setting
     * @returns void
     */
    function store(name, val) {
        if (typeof (Storage) !== 'undefined') {
            localStorage.setItem(name, val)
        }
        else {
            window.alert('Please use a modern browser to properly view this template!')
        }
    }

    /**
     * Replaces the old skin with the new skin
     * @param String cls the new skin class
     * @returns Boolean false to prevent link's default action
     */
    function changeSkin(cls) {
        $.each(mySkins, function (i) {
            $('body').removeClass(mySkins[i])
        })
        $('body').addClass(cls)
        store('skin', cls)
        return false
    }

    function setup() {
        var tmp = get('skin')
        if (tmp && $.inArray(tmp, mySkins)) changeSkin(tmp)
            // Add the change skin listener
        $('[data-skin]').on('click', function (e) {
            if ($(this).hasClass('knob')) return
            e.preventDefault()
            changeSkin($(this).data('skin'))
        })
    }
    setup();
    $("#themecolors").on("click", "a", function () {
        $("#themecolors li a").removeClass("working"),
        $(this).addClass("working")
    });
    // For Custom File Input
    $('.custom-file-input').on('change',function(){
        //get the file name
        var fileName = $(this).val();
        //replace the "Choose a file" label
        $(this).next('.custom-file-label').html(fileName);
    });

    /***Cutom js***/
    if ($('.home-custom-cards').length > 0) {
        $('.home-custom-cards').on('click', '.card', function(e){
            e.preventDefault();
            if ($('.home-custom-cards .card').hasClass('active')) {
                $('.home-custom-cards .card').removeClass('active');
            }
            $(this).addClass('active');
            var url = $(this).data('url');
            window.location.href = url;
        });
    }

    if ($('table').length > 0) {
        $('table').simpleTreeTable();
        }
    if ($('table#collapsed').length > 0) {
        $('table#collapsed').simpleTreeTable({ opened: [1] });//{ opened: [1] }
        $("table#collapsed tr.has-comparison-data > td:first-child .tree-icon").after('<a href="#" class="graphicon"></a>');
        $('a.graphicon').attr("data-toggle","modal").attr("data-target","#scenarioComparisonGraph");
        $("table#collapsed tr.has-comparison-data > td:first-child .tree-icon").on('click', function(){
            if (!$(this).parents('tr').hasClass('active')) {
                $(this).parents('tr').addClass('active');
            }else{$(this).parents('tr').removeClass('active');}
        });
        $("table#collapsed tr.has-comparison-data").on('dblclick', function(){
            $("#scenarioComparisonGraph").modal('show');
            if (!$(this).hasClass('active')) {
                $(this).addClass('active');
            }
        });
    }
    if ($(".select2").length > 0) {
        $(".select2").select2();
    }
    if ($('.selectpicker').length > 0) {
        $('.selectpicker').selectpicker();
    }

    $('.maindropdown').on('click',function(){
        if ($(this).hasClass('active')) {
             $('.main-dropdown-menu').hide();
             $(this).removeClass('active');
        }else{
        $(this).addClass('active');
        $('.main-dropdown-menu').show();

        }
    });

});
