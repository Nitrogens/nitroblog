window.onload = function() {
    var father = document.getElementById("article_cid");
    var checkboxList = document.getElementsByName("article_cid[]");

    father.onclick = function() {
        for (var i = 0; i < checkboxList.length; i++) {
            checkboxList[i].checked = this.checked;
        }
    }
}