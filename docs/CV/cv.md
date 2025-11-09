<div id="cv-content"></div>

<script>
fetch('/CV/cv_content.html')
  .then(r => r.ok ? r.text() : Promise.reject())
  .then(html => {
    document.getElementById('cv-content').innerHTML = html;
  })
  .catch(() => {
    document.getElementById('cv-content').innerHTML = 
      '<iframe src="/_artifacts/wilner_cv.pdf" width="100%" height="800px" style="border: none;"></iframe>';
  });
</script>

[Download PDF version](/_artifacts/wilner_cv.pdf)