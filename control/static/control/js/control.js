window.onload = function() {
    father = document.getElementById("article_cid");
    checkboxList = document.getElementsByName("article_cid[]");

    father.onclick = function() {
        for (var i = 0; i < checkboxList.length; i++) {
            checkboxList[i].checked = this.checked;
        }
    }
}