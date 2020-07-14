let template_id;
let data_table_id;

function upload(file, callback, processBar, tablePreview = false) {
    // let url = window.location.origin + "/upload"
    var formData = new FormData();

    formData.append("file", file);
    if (tablePreview) {
        formData.append('table-preview', true)
    }
    var req = new XMLHttpRequest();
    req.upload.addEventListener("progress", function(event) {
        var percent = (event.loaded / event.total) * 100;
        console.log(percent)
        processBar.val(Math.round(percent));
    }, false);

    req.open("POST", "/upload", true);

    req.onload = function(event) {
        if (req.status == 200) {
            console.log(JSON.parse(req.response))
            callback(JSON.parse(req.response));
            console.log("Uploaded!");
        } else {
            console.log("Error " + req.status + " occurred when trying to upload your file.<br \/>");
        }
    };
    req.send(formData);
}

function uploadTemplate() {
    // check if no file chosen, or extension not supported
    if ($('#template-file')[0].files.length == 0) {
        alert("No file chosen");
        return;
    }
    let file = $('#template-file')[0].files[0];
    if (['docx', 'odt'].indexOf(file.name.split('.').pop()) == -1) {
        console.log(file.name.split('.').pop())
        alert("File extension is not supported");
        return;
    }
    $('#progress-template').val(0)
    upload(file, function(res) {
        template_id = res.file_id;
        $('#template-next-group, #template-preview').toggleClass('d-none', false);
        $('#btn-upload-template').toggleClass('btn-primary', false).toggleClass('btn-secondary', true)
            // show preview if not on localhost   
        let url = "https://docs.google.com/gview?url=" + window.location.origin + "/files?file_id=" + template_id + "&embedded=true";
        if (window.location.hostname != "localhost") {
            $('#iframe-template-preview').attr('src', url)
        } else {
            console.log(url)
        }
    }, $('#progress-template'))
}

function uploadData() {
    // check if no file chosen, or extension not supported
    if ($('#data-table-file')[0].files.length == 0) {
        alert("No file chosen");
        return;
    }
    let file = $('#data-table-file')[0].files[0]
    if (['xlsx', 'csv', 'xls'].indexOf(file.name.split('.').pop()) == -1) {
        alert("File extension is not supported");
        return;
    }

    $('#progress-data-table').val(0)
    upload(file, function(res) {
        data_table_id = res.file_id;

        // show data table from vals returned from server
        let table = `<table class='table table-bordered'>`
        res.data.reduce(function(accumulator, current, index) {
            table += '<tr>'
            if (index == 0) {
                for (val of current) {
                    table += `<th>${val}</th>`
                }
            } else {
                for (val of current) {
                    table += `<td>${val}</td>`
                }
            }
            table += '</tr>'
        }, table)
        table += '</table>'

        $('#div-data-table-preview').html(table)


        $('#data-next-group, #data-table-preview').toggleClass('d-none', false);
        $('#btn-upload-data').toggleClass('btn-primary', false).toggleClass('btn-secondary', true)

    }, $('#progress-data-table'), true)
}

function activeTabDataTable() {
    if (template_id) {
        var pills_tab = $('#pills-datatable-tab');
        pills_tab.toggleClass('disabled', false);
        pills_tab.tab('show');
    }
}

function activeTabRender() {
    if (data_table_id) {
        var pills_tab = $('#pills-render-tab');
        pills_tab.toggleClass('disabled', false);
        pills_tab.tab('show');
    }
}

function activeTabResult() {
    var pills_tab = $('#pills-result-tab');
    pills_tab.toggleClass('disabled', false);
    pills_tab.tab('show');
}



function resetForms() {
    template_id = null;
    data_table_id = null;

    $('#pills-template-tab').tab('show');
    $('#pills-datatable-tab, #pills-render-tab, #pills-result-tab').toggleClass('disabled', true);
    $('#template-next-group, #data-next-group, #template-preview, #data-table-preview').toggleClass('d-none', true);

    $('#iframe-template-preview, #iframe-data-table-preview').attr('src', "about:blank")
    $('#progress-template, #progress-data-table').val(0);

    $('#btn-upload-template, #btn-upload-data').toggleClass('btn-primary', true).toggleClass('btn-secondary', false)

}

function applyTestData() {
    template_id = '5f09e79681a8d0768cf72fb6'
    data_table_id = '5f09bcf9ddd3a4cdb98cb1a2'
    var pills_tab = $('#pills-datatable-tab');
    pills_tab.toggleClass('disabled', false);
    var pills_tab = $('#pills-render-tab');
    pills_tab.toggleClass('disabled', false);
    var pills_tab = $('#pills-result-tab');
    pills_tab.toggleClass('disabled', false);
    $('#template-next-group, #template-preview').toggleClass('d-none', false);
    $('#data-next-group, #data-table-preview').toggleClass('d-none', false);
}

function appendJinjaTag(element) {
    document.getElementById('filename-template').value += `{{ ${element.value} }}`
}

function verifyTemplate() {
    if (!template_id || !data_table_id) return;
    $('#loadingModal').modal('show')
        // send request to verify-url with template_id and data_table_id and put result to #verificationResult
    var formData = new FormData();

    formData.append("template-id", template_id);
    formData.append("data-table-id", data_table_id);

    formData.append("name-pattern", data_table_id);

    var req = new XMLHttpRequest();

    req.open("POST", "/verify", true);

    req.onload = function(event) {
        if (req.status == 200) {
            var res = JSON.parse(req.response)

            if (res.status == 'err') {
                alert('Something wrong occurred')
            } else {

                let div_verification = document.getElementById('verificationResult')

                if (res.messages.length == 0) {
                    div_verification.innerHTML = `Verification done without warning`
                } else {
                    div_verification.innerHTML = ''
                    for (message of res.messages) {
                        div_verification.innerHTML += `<p>${message}</p>`
                    }
                }
                document.getElementById('filename-template').value = `{{ ${res.fields[0]} }}`

                let div_fields = document.getElementById('field-list')
                div_fields.innerHTML = ''
                for (field of res.fields) {
                    div_fields.innerHTML += `<input type='button' onclick='appendJinjaTag(this)' value='${field}'/>`
                }

                activeTabRender()
            }
        } else {
            console.log("Error " + req.status + " occurred");
        }
        $('#loadingModal').modal('hide')
    };
    req.send(formData);
}

function generateResult() {
    if (!template_id || !data_table_id) return;
    $('#loadingModal').modal('show')
        // send request to render-url with template_id and data_table_id and put result to #renderResult
    var formData = new FormData();

    formData.append("template-id", template_id);
    formData.append("data-table-id", data_table_id);
    let name_template = document.getElementById('filename-template').value;
    if (name_template.length != 0) {
        formData.append("name-pattern", name_template);
    }
    var req = new XMLHttpRequest();

    req.open("POST", "/render", true);

    req.onload = function(event) {
        if (req.status == 200) {
            var res = JSON.parse(req.response)

            if (res.status == 'err') {
                alert('Something wrong occurred')
            } else {

                let div_result = document.getElementById('renderResult')
                div_result.innerHTML = 'Generated files:<br /><ul>'
                Object.keys(res.files).forEach(function(filename) {
                    div_result.innerHTML += `<li><a href='/files?file_id=${res.files[filename]}'>${filename}</a></li>`
                });
                div_result.innerHTML += '</ul><br />Download all as archive: '
                div_result.innerHTML += `<a href='/files?file_id=${res.archive}'>Link</a></li>`

                activeTabResult()
            }
        } else {
            console.log("Error " + req.status + " occurred");
        }
        $('#loadingModal').modal('hide')
    };
    req.send(formData);
}