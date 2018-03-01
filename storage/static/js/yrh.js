/**
 * Created by ronghuayao on 2017/11/3.
 */


String.prototype.format = function () {
    var args = arguments;
    if (!args.length) return this;
    if (typeof args[0] == "object") {
        args = args[0];
    }
    return this.replace(/\{([^\}]+)\}/g,
        function (m, i) {
            var val = args ? args[i] : '';
            return val == null || val == undefined ? '' : val;
        });
}

Date.prototype.format = function (fmt) {
    // author: meizz
    var o = {
        "M+": this.getMonth() + 1, // 月份
        "d+": this.getDate(), // 日
        "h+": this.getHours(), // 小时
        "m+": this.getMinutes(), // 分
        "s+": this.getSeconds(), // 秒
        "q+": Math.floor((this.getMonth() + 3) / 3), // 季度
        "S": this.getMilliseconds()
        // 毫秒
    };
    if (/(y+)/.test(fmt))
        fmt = fmt.replace(RegExp.$1, (this.getFullYear() + "").substr(4
            - RegExp.$1.length));
    for (var k in o)
        if (new RegExp("(" + k + ")").test(fmt))
            fmt = fmt.replace(RegExp.$1, (RegExp.$1.length == 1)
                ? (o[k])
                : (("00" + o[k]).substr(("" + o[k]).length)));
    return fmt;
}

Date.prototype.addDays = function (d) {
    this.setDate(this.getDate() + d);
    return this;
};

Date.prototype.addMonths = function (m) {
    this.setMonth(this.getMonth() + m);
    return this;
};

Date.prototype.getWeek = function () {
    var onejan = new Date(this.getFullYear(), 0, 1);
    return Math.ceil((((this - onejan) / 86400000) + onejan.getDay() - 1) / 7);
};

function Log(val) {
    console.log(val);
}