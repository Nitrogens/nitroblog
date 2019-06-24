$(document).ready(function () {
    $(".comment-reply").click(function () {
        var id = $(event.currentTarget).attr("id");
        $(".modal-body #id_id").val(id);
    });
});

window.onload = function() {
    father = document.getElementById("article_cid");
    checkboxList = document.getElementsByName("article_cid[]");

    father.onclick = function() {
        for (var i = 0; i < checkboxList.length; i++) {
            checkboxList[i].checked = this.checked;
        }
    }
}