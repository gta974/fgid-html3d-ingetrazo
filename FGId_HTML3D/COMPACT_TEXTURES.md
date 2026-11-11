# Compact HTML textures

Opaque textures are encoded as JPEG quality 85 when smaller than PNG. Existing JPEGs are kept byte-for-byte. Actual transparency, including partial opacity, stays lossless in PNG. Image dimensions and UV coordinates are unchanged. Duplicate encoded images are embedded once. Unsupported browser formats such as TIFF are converted to PNG/JPEG.

Compression is performed in memory during HTML export. Source texture files and the IngeTrazo model remain untouched. The standalone HTML still opens without an internet connection.

Close IngeTrazo and replace this plugin's complete folder in the plugins directory, then restart and export again. Existing HTML files must be regenerated to benefit.

Validation: Muuratsalo, saved scenes, real exporter and Chrome rendering, alpha cutouts/partial alpha, existing JPEG preservation, and full-resolution output. The supplied 14,576,367-byte HTML becomes 4,967,750 bytes.
