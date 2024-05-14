1. Unpack `.zip` files
````powershell
$sourceDirectory = Get-Location
$zipFiles = Get-ChildItem -Path $sourceDirectory -Filter *.zip -Recurse

foreach ($zipFile in $zipFiles) {
    $parentFolder = $zipFile.DirectoryName
    try {
        $destinationPath = $parentFolder
        Expand-Archive -Path $zipFile.FullName -DestinationPath $destinationPath -Force -ErrorAction Stop
        Write-Host "Extracted $($zipFile.Name) successfully to $($destinationPath)."
        
        # Extract specific file types
        $extractedFiles = Get-ChildItem -Path $destinationPath -Recurse -Include *.d64 -File
        foreach ($file in $extractedFiles) {
            Move-Item -Path $file.FullName -Destination $parentFolder -Force
            Write-Host "Moved $($file.Name) from $($file.DirectoryName) to $($parentFolder)."
        }
    } catch {
        Write-Host "Failed to extract $($zipFile.Name). Removing the file."
        Remove-Item -Path $zipFile.FullName -Force
    }
    
    # Remove all files and folders in the parent directory except zip files and specific extensions
    $itemsToRemove = Get-ChildItem -Path $parentFolder -Exclude *.zip, *.d64 -Recurse
    
    foreach ($item in $itemsToRemove) {
        Remove-Item -Path $item.FullName -Force -Recurse
        Write-Host "Removed $($item.FullName)."
    }
}

# Remove all empty folders
Get-ChildItem -Path $sourceDirectory -Directory -Recurse | Where-Object { $_.GetFileSystemInfos().Count -eq 0 } | Remove-Item -Force
````

2. Delete used `.zip` files
````powershell
$sourceDirectory = Get-Location
$zipFiles = Get-ChildItem -Path $sourceDirectory -Filter *.zip -Recurse

foreach ($zipFile in $zipFiles) {
    Remove-Item -Path $zipFile.FullName -Force
    Write-Host "Removed $($zipFile.FullName)."
}
````

3. Set all filenames to lowercase

````powershell
$sourceDirectory = Get-Location
$allFiles = Get-ChildItem -Path $sourceDirectory -Recurse -File

foreach ($file in $allFiles) {
    $newFileName = $file.FullName.ToLower()
    Rename-Item -Path $file.FullName -NewName $newFileName -Force
    Write-Host "Renamed $($file.FullName) to $($newFileName)."
}
````

4. Delete empty folders

````powershell
Get-ChildItem -Path $sourceDirectory -Directory -Recurse | Where-Object { $_.GetFileSystemInfos().Count -eq 0 } | Remove-Item -Force
````