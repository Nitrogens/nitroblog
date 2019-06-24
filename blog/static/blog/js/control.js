$(document).ready(function () {
    $(".comment-reply").click(function () {
        var id = $(event.currentTarget).attr("id");
        $(".modal-body #id_id").val(id);
    });
});