const AjaxHelper = {
    ajax: function (type, url, data, success, error) {
        $.ajax({
            type: type,
            url: API_PATH + url,
            data: data ? JSON.stringify(data) : '',
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: success,
            error: error
        });
    },

    get: function (url, success, error) {
        this.ajax("GET", url, null, success, error);
    },

    post: function (url, data, success, error) {
        this.ajax("POST", url, data, success, error);
    },

    postir: function (folder, action) {
        this.post(`/IR/${folder}/${action}`);
    },

    getir: function (folder, action) {
        this.get(`/IR/${folder}/${action}`);
    }
}

const AjaxHelper2 = {
    ajax: function (type, url, data, success, error) {
        $.ajax({
            type: type,
            url: API_PATH + url,
            data: data ? JSON.stringify(data) : '',
            //contentType: "application/json; charset=utf-8",
            //dataType: "json",
            success: success,
            error: error
        });
    },

    get: function (url, success, error) {
        this.ajax("GET", url, null, success, error);
    },

    post: function (url, data, success, error) {
        this.ajax("POST", url, data, success, error);
    },

    postir: function (folder, action) {
        this.post(`/IR/${folder}/${action}`);
    },

    getir: function (folder, action) {
        this.get(`/IR/${folder}/${action}`);
    }
}