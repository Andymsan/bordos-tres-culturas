<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.44.0" styleCategories="Symbology">
 <pipe>
  <rasterrenderer type="singlebandpseudocolor" band="1" opacity="1" alphaBand="-1" classificationMin="2010" classificationMax="2024" nodataColor="">
   <rasterTransparency/>
   <minMaxOrigin><limits>None</limits><extent>WholeRaster</extent><statAccuracy>Estimated</statAccuracy><cumulativeCutLower>0.02</cumulativeCutLower><cumulativeCutUpper>0.98</cumulativeCutUpper><stdDevFactor>2</stdDevFactor></minMaxOrigin>
   <rastershader>
    <colorrampshader colorRampType="DISCRETE" classificationMode="2" clip="0" minimumValue="2010" maximumValue="2024" labelPrecision="1">
     <item value="2014" color="#08306b" alpha="255" label="≤ 2014 · cauce / agua casi siempre"/>
     <item value="2016" color="#7f0000" alpha="255" label="2014–2016 · se inunda &gt; 57% del año (&gt; 209 días)"/>
     <item value="2017" color="#d7301f" alpha="255" label="2016–2017 · 46–57% (169–209 días)"/>
     <item value="2018" color="#fc8d59" alpha="255" label="2017–2018 · 23–46% (84–169 días)"/>
     <item value="2018.4" color="#fdcc8a" alpha="255" label="2018–2018.4 · 3–23% (13–84 días)"/>
     <item value="2019" color="#a6d96a" alpha="255" label="2018.4–2019 · &lt; 3% (raro, sep)"/>
     <item value="2020" color="#1a9641" alpha="255" label="2019–2020 · casi nunca"/>
     <item value="2022" color="#2b83ba" alpha="255" label="2020–2022 · sobre el NAME, seguro"/>
     <item value="inf" color="#e0e0e0" alpha="255" label="&gt; 2022 · terreno alto / estructuras"/>
    </colorrampshader>
   </rastershader>
  </rasterrenderer>
  <brightnesscontrast brightness="0" contrast="0" gamma="1"/>
  <huesaturation saturation="0" grayscaleMode="0" invertColors="0" colorizeOn="0" colorizeRed="255" colorizeGreen="128" colorizeBlue="128" colorizeStrength="100"/>
  <rasterresampler maxOversampling="2" zoomedInResampler="bilinear"/>
 </pipe>
 <blendMode>0</blendMode>
</qgis>
