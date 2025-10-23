param(
  [string]$BaseUrl = "http://localhost:8000",
  [string]$DataDir = ".\sample_data"
)

function Invoke-PostJson {
  param([string]$Uri, [hashtable]$Body)
  try {
    $json = ($Body | ConvertTo-Json -Depth 5)
    Invoke-RestMethod -Uri $Uri -Method POST -ContentType "application/json" -Body $json -ErrorAction Stop
  } catch {
    # Try to surface server's error text
    if ($_.Exception.Response -and $_.Exception.Response.GetResponseStream) {
      $reader = New-Object IO.StreamReader($_.Exception.Response.GetResponseStream())
      $msg = $reader.ReadToEnd()
      throw "POST $Uri failed: $msg"
    } else {
      throw
    }
  }
}

Write-Host "Uploading CSVs from $DataDir to $BaseUrl`n"

# --- 1) Courses ---
$coursesCsv = Join-Path $DataDir "courses.csv"
if (Test-Path $coursesCsv) {
  Write-Host "Creating courses..."
  $created = 0; $skipped = 0
  foreach ($row in Import-Csv $coursesCsv) {
    try {
      Invoke-PostJson -Uri "$BaseUrl/courses" -Body @{ code=$row.code; title=$row.title; term=$row.term }
      $created++
    } catch {
      if ($_ -match "Course code already exists") { $skipped++ } else { Write-Warning $_ }
    }
  }
  Write-Host " -> courses: created=$created, skipped=$skipped"
} else { Write-Warning "Missing $coursesCsv" }

# --- 2) Students ---
$studentsCsv = Join-Path $DataDir "students.csv"
if (Test-Path $studentsCsv) {
  Write-Host "Creating students..."
  $created = 0; $skipped = 0
  foreach ($row in Import-Csv $studentsCsv) {
    try {
      Invoke-PostJson -Uri "$BaseUrl/students" -Body @{ email=$row.email; full_name=$row.full_name }
      $created++
    } catch {
      if ($_ -match "Student email already exists") { $skipped++ } else { Write-Warning $_ }
    }
  }
  Write-Host " -> students: created=$created, skipped=$skipped"
} else { Write-Warning "Missing $studentsCsv" }

# --- 3) Assignments ---
$assignmentsCsv = Join-Path $DataDir "assignments.csv"
if (Test-Path $assignmentsCsv) {
  Write-Host "Creating assignments..."
  $created = 0; $skipped = 0; $errors = 0
  foreach ($row in Import-Csv $assignmentsCsv) {
    try {
      # Expect headers: course_code,name,type,max_points
      Invoke-PostJson -Uri "$BaseUrl/assignments" -Body @{
        course_code = $row.course_code
        name        = $row.name
        type        = $row.type    # quiz|test|project
        max_points  = [int]$row.max_points
      }
      $created++
    } catch {
      if ($_ -match "Assignment name already exists in course") { $skipped++ }
      elseif ($_ -match "Course not found") { Write-Warning "Course missing for assignment '$($row.name)' in course '$($row.course_code)'"; $errors++ }
      else { Write-Warning $_; $errors++ }
    }
  }
  Write-Host " -> assignments: created=$created, skipped=$skipped, errors=$errors"
} else { Write-Warning "Missing $assignmentsCsv" }

# --- 4) Grades ---
$gradesCsv = Join-Path $DataDir "grades.csv"
if (Test-Path $gradesCsv) {
  Write-Host "Uploading grades..."
  $uploadUri = "$BaseUrl/grades/upload"
  $usedBulk = $false
  try {
    # If your API has /grades/upload, this will work; otherwise it will 404 and fall back to per-row
    $resp = Invoke-RestMethod -Uri $uploadUri -Method POST -Form @{ file = Get-Item $gradesCsv } -ErrorAction Stop
    Write-Host (" -> grades via /upload: created={0}, updated={1}, errors={2}" -f $resp.created, $resp.updated, ($resp.errors.Count))
    $usedBulk = $true
  } catch {
    if ($_ -match "Not Found") {
      Write-Host "Bulk /grades/upload not found. Falling back to per-row POST /grades..."
    } else {
      Write-Warning "Bulk upload failed. Falling back to per-row. Error: $_"
    }
  }

  if (-not $usedBulk) {
    $created = 0; $updated = 0; $errors = 0
    foreach ($row in Import-Csv $gradesCsv) {
      try {
        Invoke-PostJson -Uri "$BaseUrl/grades" -Body @{
          course_code     = $row.course_code
          student_email   = $row.student_email
          assignment_name = $row.assignment_name
          points          = [int]$row.points
        }
        $created++  # treat as created/upsert; we don't differentiate updated here
      } catch {
        if ($_ -match "Points cannot exceed max_points") { Write-Warning "points>max for $($row.student_email) / $($row.assignment_name)"; $errors++ }
        elseif ($_ -match "Assignment not found") { Write-Warning "Missing assignment '$($row.assignment_name)' in '$($row.course_code)'"; $errors++ }
        elseif ($_ -match "Course or student not found") { Write-Warning "Missing course/student for row: $($row | ConvertTo-Json -Compress)"; $errors++ }
        else { Write-Warning $_; $errors++ }
      }
    }
    Write-Host " -> grades (per-row): ok=$created, errors=$errors"
  }
} else { Write-Warning "Missing $gradesCsv" }

Write-Host "`nDone."
