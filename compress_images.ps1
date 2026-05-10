Add-Type -AssemblyName System.Drawing
function Compress-Image {
    param(
        [string]$InputPath,
        [string]$OutputPath,
        [int]$Quality = 60,
        [int]$MaxWidth = 1920
    )
    if (-Not (Test-Path $InputPath)) { return }
    $img = [System.Drawing.Image]::FromFile($InputPath)
    $ratio = $img.Width / $img.Height
    $newWidth = [Math]::Min($img.Width, $MaxWidth)
    $newHeight = [int]($newWidth / $ratio)
    
    $bmp = new-object System.Drawing.Bitmap($newWidth, $newHeight)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.DrawImage($img, 0, 0, $newWidth, $newHeight)
    
    $encoder = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | where {$_.MimeType -eq 'image/jpeg'}
    $params = new-object System.Drawing.Imaging.EncoderParameters(1)
    $params.Param[0] = new-object System.Drawing.Imaging.EncoderParameter([System.Drawing.Imaging.Encoder]::Quality, $Quality)
    
    $bmp.Save($OutputPath, $encoder, $params)
    
    $g.Dispose()
    $bmp.Dispose()
    $img.Dispose()
}

$root = "c:\yachts-atlas"
$public = "$root\frontend\public"

Compress-Image -InputPath "$root\ai-generated-boat-picture.jpg" -OutputPath "$public\boat-picture-light.jpg" -Quality 50 -MaxWidth 1600
Compress-Image -InputPath "$root\ai-generated-boat-picture (1).jpg" -OutputPath "$public\boat-picture-2-light.jpg" -Quality 50 -MaxWidth 1600
Compress-Image -InputPath "$root\moored-yacht-mediterranean-sea-port-buildings-street-greenery-barcelona-spain.jpg" -OutputPath "$public\barcelona-yacht-light.jpg" -Quality 50 -MaxWidth 1600
