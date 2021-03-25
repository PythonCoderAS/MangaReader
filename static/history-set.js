Storage.prototype.setObj = function (key, obj) {
    return this.setItem(key, JSON.stringify(obj))
}
Storage.prototype.getObj = function (key) {
    const item = this.getItem(key);
    if (item !== undefined){
        return JSON.parse(item)
    } else {
        return null;
    }
}

const pathArray = window.location.pathname.split('/');
const mangaName = pathArray[1];

const existingData = window.localStorage.getObj(mangaName) || [];
if (!existingData.includes(pathArray[2])){
    existingData[existingData.length] = pathArray[2];
    window.localStorage.setObj(mangaName, existingData);
}
