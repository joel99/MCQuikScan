//Custom js

//DOM selectors

const fileInput = document.getElementById('upload-input')
const label = fileInput.nextElementSibling
const status = document.getElementById('status-text')
const preview = document.getElementById('preview-img')
const uploadBtn = document.getElementById('upload-button')
const resultContainer = document.getElementById('result')

let validUpload = false

//Update status
const allowedExt = ['jpg', 'jpeg', 'png']

fileInput.addEventListener( 'change', function( e ) {
  let fileName = ''
  if ( this.files ) {
    fileName = e.target.value.split( '\\' ).pop()
    //sanitize
    const ext = fileName.split('.').pop()
    if ( allowedExt.includes(ext) ) {
      label.innerHTML = fileName
      status.innerHTML = "File selected"      
      preview.src = URL.createObjectURL(e.target.files[0])
      validUpload = true
    } else {
      label.innerHTML = "Select File"
      if (fileName = '') status.innerHTML = "No file selected."
      else status.innerHTML = fileName + " has an invalid file extension. Upload JPG, JPEG, or PNG"
      validUpload = false
    }
  }
})

//upload listener
uploadBtn.addEventListener( 'click', function( e ) {
  e.preventDefault()
  let files = fileInput.files
  if (files && validUpload) {
    let file = files[0]
    let formData = new FormData()
    formData.append("upload", file)
    let xhr = new XMLHttpRequest()
    xhr.onprogress = function (e) {
      //processing
      status.innerHTML = 'Processing image...'
    }

    xhr.onload = function (e) {
      //success
      resultContainer.innerHTML = "";
      data = JSON.parse(e.target.response)
      status.innerHTML = 'Image processed. Results below.'
      console.log(data)
      if (data["text"] === "fail" || data["qN"] === undefined) resultContainer.innerHTML = "Image processing failed."
      else {
	let qN = document.createElement('h4')
	qN.innerHTML = "Question " + data["qN"] + ":"
	resultContainer.appendChild(qN)
	for (let i = 0; i < data["choices"].length; i++) {
	  let curChoice = document.createElement('p')
	  curChoice.innerHTML = data["choices"][i].toUpperCase()
	  resultContainer.appendChild(curChoice)
	}
      }
    }

    xhr.onerror = function (e) {
      status.innerHTML = 'Upload error, please try again.'
    }

    xhr.open('POST', '/upload/', true)

    xhr.send(formData)
  }  
})
