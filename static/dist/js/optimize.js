$(function () {
    $(".bootstrap-tagsinput input").on("focus", function () {
        $(".bootstrap-tagsinput").animate({opacity: 1.0,}, 1500,"linear" ).css("border-bottom", "2px solid #037dae","transition", "opacity 3s ease-in-out", "transition-duration","3s");          
    });
    $(".bootstrap-tagsinput input").on("blur", function () {
        $(".bootstrap-tagsinput").animate({opacity: 1.0}, 1500,"linear" ).css("border-bottom", "1px solid #e9ecef");          
    });
    $(".assetsIP").on("focus", function () {
        $(this).animate({opacity: 1.0,}, 1500,"linear" ).css("border-bottom", "2px solid #037dae","transition", "opacity 3s ease-in-out", "transition-duration","3s");          
    });
    $(".assetsIP").on("blur", function () {
        $(this).animate({opacity: 1.0}, 1500,"linear" ).css("border-bottom", "1px solid #e9ecef");          
    });
});