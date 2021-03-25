Storage.prototype.setObj = function (key, obj) {
    return this.setItem(key, JSON.stringify(obj))
}
Storage.prototype.getObj = function (key) {
    const item = this.getItem(key);
    if (item !== undefined) {
        return JSON.parse(item)
    } else {
        return null;
    }
}

const pathArray = window.location.pathname.split('/');
const mangaName = pathArray[1];

const existingData = window.localStorage.getObj(mangaName) || [];
const listItems = document.querySelectorAll("li a");
for (let num = 0; num < listItems.length; num++) {
    const parts = listItems[num].href.split("/");
    const chapter_name = parts[parts.length - 1];
    if (existingData.includes(chapter_name)) {
        listItems[num].classList.add("visited");
    }
}
