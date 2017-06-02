// 기본 세팅 
	$(document).ready(function() {
  		$('#size_overall').prop("checked", true);
		$('#categoryAll').prop("checked", true);
	}); // document 끝 



// 숫자 function	
function formatNumber (num) {
    return num.toString().replace(/(\d)(?=(\d{3})+(?!\d))/g, "$1  ")
};


// 지도 
var map = L.map('map').setView([6.5486547,3.2570718], 5);
  
// 데이터 파일 로딩 
function readfile (filename) {
	$.getJSON("./data/SWAC.geojson", function(statesData) {
 
	var yearAmap = statesData; // 지도데이터 저장 
			mapDraw(yearAmap); 
			

	function mapDraw(event) {  
			var basemap = L.tileLayer('https://api.mapbox.com/styles/v1/mkmd/cj3cqvimu00002rnz5z4cptmc/tiles/256/{z}/{x}/{y}@2x?access_token=pk.eyJ1IjoibWttZCIsImEiOiJjajBqYjJpY2owMDE0Mndsbml0d2V1ZXczIn0.el8wQmA-TSJp2ggX8fJ1rA', {
				
			//var basemap = L.tileLayer('https://api.mapbox.com/styles/v1/mkmd/cj0jb3nex00i02smnqy5v1upb/tiles/256/{z}/{x}/{y}@2x?access_token=pk.eyJ1IjoibWttZCIsImEiOiJjajBqYjJpY2owMDE0Mndsbml0d2V1ZXczIn0.el8wQmA-TSJp2ggX8fJ1rA', {
					minZoom: 3,
					maxZoom: 11
					}).addTo(map); 
		
			
			// 범죄별 지도 한 장 = 레이어 한 장. 범죄 항목을 선택할 때마다 레이어를 hide/show
			
			
			var City_Size_cluster = new L.MarkerClusterGroup(event,{showCoverageOnHover: false});  
			var City_Size =  L.geoJson(event, {onEachFeature: onEachFeature });  			
			var Market_Potential =  L.geoJson(event, {onEachFeature: onEachFeature});  
			var Local_Dominance =  L.geoJson(event, {onEachFeature: onEachFeature});  

			// City_Size
			var size_overall = L.geoJson(event, {onEachFeature: onEachFeature});
			var size_10000 = L.geoJson(event,{filter:size_10000, onEachFeature: onEachFeature});
			var size_30000 = L.geoJson(event,{filter:size_30000, onEachFeature: onEachFeature});
			var size_100000 = L.geoJson(event,{filter:size_100000, onEachFeature: onEachFeature});
			var size_350000 = L.geoJson(event,{filter:size_350000, onEachFeature: onEachFeature});
			var size_1mil = L.geoJson(event,{filter:size_1mil, onEachFeature: onEachFeature});
			var size_2mil = L.geoJson(event,{filter:size_2mil, onEachFeature: onEachFeature});
			// City_Group
			var Global =  L.geoJson(event, {filter: Global, onEachFeature: onEachFeature});  
			var Regional =  L.geoJson(event, {filter: Regional, onEachFeature: onEachFeature});  
			var Metro =  L.geoJson(event, {filter: Metro, onEachFeature: onEachFeature});  
			var Satellite =  L.geoJson(event, {filter: Satellite, onEachFeature: onEachFeature});  
			var Local =  L.geoJson(event, {filter: Local, onEachFeature: onEachFeature});  
			var RuralT =  L.geoJson(event, {filter: RuralT, onEachFeature: onEachFeature});  
			var RuralC =  L.geoJson(event, {filter: RuralC, onEachFeature: onEachFeature});  

			
			///////////////////////////////////////////////////////////////////// function
			function Global(feature) {
			if (feature.properties.Cluster_group === " Global African Cities ") return true
			};
			function Regional(feature) {
			if (feature.properties.Cluster_group === " Regional Cities ") return true
			};
			function Metro(feature) {
			if (feature.properties.Cluster_group === " Metropolitan Areas ") return true
			};
			function Satellite(feature) {
			if (feature.properties.Cluster_group === " Satellite Town ") return true
			};
			function Local(feature) {
			if (feature.properties.Cluster_group === " Local Cities ") return true
			};
			function RuralT(feature) {
			if (feature.properties.Cluster_group === " Rural Town ") return true
			};
			function RuralC(feature) {
			if (feature.properties.Cluster_group === " Rural Clusters ") return true
			};
			////
			function size_10000(feature) {
			if (feature.properties.CitySize_category === "10~30") return true
			};
			function size_30000(feature) {
			if (feature.properties.CitySize_category === "30~100") return true
			};
			function size_100000(feature) {
			if (feature.properties.CitySize_category === "100~350") return true
			};
			function size_350000(feature) {
			if (feature.properties.CitySize_category === "350~1000") return true
			};
			function size_1mil(feature) {
			if (feature.properties.CitySize_category === "1000~2000") return true
			};
			function size_2mil(feature) {
			if (feature.properties.CitySize_category === "Above2000") return true
			};
			///////////////////////////////////////////////////////////////////// function end


			// 기본 범죄 지도 
			City_Size_cluster.addLayer(size_overall);
			map.addLayer(City_Size_cluster);
			//City_Size_cluster.addTo(map);
			// 지도 지역 라벨 
		 
			// 각 범죄 항목을 선택하면 지도 변경
			$('input:radio[name="crimeSelected"]').change(function(){
				
				// 전체 레이어를 지우고 다시 추가 
				
 
				if($('input:radio[name="crimeSelected"]:input[value=Global]').is(":checked"))  {  map.removeLayer(City_Size_cluster); City_Size_cluster.clearLayers();City_Size_cluster.addLayer(Global); map.addLayer(City_Size_cluster); }  
				if($('input:radio[name="crimeSelected"]:input[value=Regional]').is(":checked"))  {  map.removeLayer(City_Size_cluster); City_Size_cluster.clearLayers();City_Size_cluster.addLayer(Regional);map.addLayer(City_Size_cluster) }  
				if($('input:radio[name="crimeSelected"]:input[value=Metro]').is(":checked"))  {  map.removeLayer(City_Size_cluster); City_Size_cluster.clearLayers();City_Size_cluster.addLayer(Metro);map.addLayer(City_Size_cluster) }  
			    if($('input:radio[name="crimeSelected"]:input[value=Satellite]').is(":checked"))  {  map.removeLayer(City_Size_cluster);City_Size_cluster.clearLayers(); City_Size_cluster.addLayer(Satellite);map.addLayer(City_Size_cluster) }  
				if($('input:radio[name="crimeSelected"]:input[value=Local]').is(":checked"))  {  map.removeLayer(City_Size_cluster);City_Size_cluster.clearLayers(); City_Size_cluster.addLayer(Local);map.addLayer(City_Size_cluster) }  
				if($('input:radio[name="crimeSelected"]:input[value=RuralT]').is(":checked"))  {  map.removeLayer(City_Size_cluster);City_Size_cluster.clearLayers(); City_Size_cluster.addLayer(RuralT);map.addLayer(City_Size_cluster) }  
				if($('input:radio[name="crimeSelected"]:input[value=RuralC]').is(":checked"))  {  map.removeLayer(City_Size_cluster);City_Size_cluster.clearLayers(); City_Size_cluster.addLayer(RuralC);map.addLayer(City_Size_cluster) }  
			                 
				if($('input:radio[name="crimeSelected"]:input[value=size_overall]').is(":checked"))  {  map.removeLayer(City_Size_cluster);City_Size_cluster.clearLayers();City_Size_cluster.addLayer(size_overall); map.addLayer(City_Size_cluster) }  			 
				if($('input:radio[name="crimeSelected"]:input[value=size_10000]').is(":checked"))  {  map.removeLayer(City_Size_cluster);City_Size_cluster.clearLayers();City_Size_cluster.addLayer(size_10000); map.addLayer(City_Size_cluster) }  
				if($('input:radio[name="crimeSelected"]:input[value=size_30000]').is(":checked"))  {  map.removeLayer(City_Size_cluster);City_Size_cluster.clearLayers();City_Size_cluster.addLayer(size_30000); map.addLayer(City_Size_cluster) }  
				if($('input:radio[name="crimeSelected"]:input[value=size_100000]').is(":checked"))  {  map.removeLayer(City_Size_cluster);City_Size_cluster.clearLayers();City_Size_cluster.addLayer(size_100000); map.addLayer(City_Size_cluster) }  
				if($('input:radio[name="crimeSelected"]:input[value=size_350000]').is(":checked"))  {  map.removeLayer(City_Size_cluster);City_Size_cluster.clearLayers();City_Size_cluster.addLayer(size_350000); map.addLayer(City_Size_cluster) }  
				if($('input:radio[name="crimeSelected"]:input[value=size_1mil]').is(":checked"))  {  map.removeLayer(City_Size_cluster);City_Size_cluster.clearLayers();City_Size_cluster.addLayer(size_1mil); map.addLayer(City_Size_cluster) }  
				if($('input:radio[name="crimeSelected"]:input[value=size_2mil]').is(":checked"))  {  map.removeLayer(City_Size_cluster);City_Size_cluster.clearLayers();City_Size_cluster.addLayer(size_2mil); map.addLayer(City_Size_cluster) }  				
			});


			
			
			//map.dragging.disable(); // 드래그 금지
			//map.zoomControl.remove(); // zoom 버튼 삭제 
  
  			

		 	// 마우스를 올리거나 터치했을 때 이벤트 
			function highlightFeature(e) {
				var layer = e.target;
				///////chartChange();
				$('#dashboard').show();
			




			document.getElementById("labelExplainBoxtitle").innerHTML = (e.target.feature.properties.Cluster_group);

			function colcol() {
			if (e.target.feature.properties.Cluster_group === " Global African Cities ") return "rgba(202,42,29,0.6)"
			if (e.target.feature.properties.Cluster_group === " Regional Cities ") return "rgba(0,127,189,0.6)"
			if (e.target.feature.properties.Cluster_group === " Metropolitan Areas ") return "rgba(252,207,0,0.6)"
			if (e.target.feature.properties.Cluster_group === " Satellite Town ") return "rgba(141,45,177,0.6)"
			if (e.target.feature.properties.Cluster_group === " Local Cities ") return "rgba(241,126,0,0.6)"
			if (e.target.feature.properties.Cluster_group === " Rural Town ") return "rgba(191,220,54,0.6)"
			if (e.target.feature.properties.Cluster_group === " Rural Clusters ") return "rgba(0,172,67,0.6)"
			};
			
			function borcol() {
			if (e.target.feature.properties.Cluster_group === " Global African Cities ") return "rgba(202,42,29,1)"
			if (e.target.feature.properties.Cluster_group === " Regional Cities ") return "rgba(0,127,189,1)"
			if (e.target.feature.properties.Cluster_group === " Metropolitan Areas ") return "rgba(252,207,0,1)"
			if (e.target.feature.properties.Cluster_group === " Satellite Town ") return "rgba(141,45,177,1)"
			if (e.target.feature.properties.Cluster_group === " Local Cities ") return "rgba(241,126,0,1)"
			if (e.target.feature.properties.Cluster_group === " Rural Town ") return "rgba(191,220,54,1)"
			if (e.target.feature.properties.Cluster_group === " Rural Clusters ") return "rgba(0,172,67,1)"
			};
			
			SWACdata = {
				labels: ['City size', 'Market potential', 'Level of urbanization', 'Local dominance'],
				datasets: [{label: e.target.feature.properties.Names,
				data: [(Math.log10(e.target.feature.properties.City_Size)-Math.log10(10000))/3.0248,(Math.log10(e.target.feature.properties.Market_Potential)-Math.log10(12573))/3.1473,e.target.feature.properties.Urban_Rate,e.target.feature.properties.Local_Dominance]
					,"backgroundColor":colcol(),"borderColor":borcol()}
				]
				};
			////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
				
				var myRadarChart = new Chart(document.getElementById("myChart"),{
				type: 'radar',data:SWACdata,
				
				options:{responsive:true,borderColor:"red",
					scale: {
					// Hides the scale
					display: true
					}
					}
					});
					
			
			function myFunction(){document.getElementById("labelExplainBox").innerHTML = ('<center>'+'<p class="tableLocationin">'+ e.target.feature.properties.ISO3 +'<br>'+ e.target.feature.properties.Names + '</p>'+
					'<table id="popupin">' +
			       		'<tr>'+
			       			'<td class="tabletitle">Variables</td>'+
			       			'<td class="tabletitles">Value</td>'+ 
			       		'</tr>'+
			       		'<tr>'+
			       			'<td class="tabledata">City Size</td>'+
			       			'<td class="tabledatas">'+(formatNumber(e.target.feature.properties.City_Size))+'</td>'+
			       		'</tr>'+
			       		'<tr>'+
			       			'<td class="tabledata">Market Potential</td>'+
			       			'<td class="tabledatas">'+(formatNumber(e.target.feature.properties.Market_Potential))+'</td>'+
			       		'</tr>'+
			       		'<tr>'+
			       			'<td class="tabledata">Urbanisation Level</td>'+
			       			'<td class="tabledatas">'+(e.target.feature.properties.Urban_Rate).toFixed(2)+'</td>'+
			       		'</tr>'+
			       		'<tr>'+
			       			'<td class="tabledata">Local Dominance</td>'+
			       			'<td class="tabledatas">'+(e.target.feature.properties.Local_Dominance).toFixed(2)+'</td>'+
			       		'</tr>'+
			       		'<tr>'+
			       			'<td class="tabledata">Growth Rate</td>'+
			       			'<td class="tabledatas">'+(e.target.feature.properties.GrowthRate).toFixed(2)+'</td>'+
			       		'</tr>' +
						'<tr>'+
						'<td class="tabledata">ID</td>'+
			       		'<td class="tabledatas">'+(e.target.feature.properties.Agglomeration_ID)+'</td>'+
						'</tr>'+
			       		'<tr>'+
						'<td class="tabledata">Lon</td>'+
			       		'<td class="tabledatas">'+(e.target.feature.properties.Lon).toFixed(2)+'</td>'+
						'</tr>'+
			       		'<tr>'+
						'<td class="tabledata">Lat</td>'+
			       		'<td class="tabledatas">'+(e.target.feature.properties.Lat).toFixed(2)+'</td>'+
						'</tr>'+
			'</table>'+'</center>')};
			myFunction();



////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

			
				this.openPopup();
			}
 
			// 원래 상태로 돌아갔을 때 이벤트 
			function resetHighlight(e) {
				var layer = e.target;
			
			//$('#dashboard').hide();	
				
				this.closePopup();
			}

			// 지도 인터랙션 함수. 팝업 / 지도 라벨 등 
			function onEachFeature(feature, layer) {
				layer.on({
					mouseover: highlightFeature,
					mouseout: resetHighlight 
				}); 

				 
				////////////////
			
		/////////////////////////////////////////////
		//	var myRadarChart = new Chart(document.getElementById("myChart"),{
		//		type: 'radar',
		//		data: {
		//		labels: ['City size', 'Market potential', 'Level of urbanization', 'Local dominance'],
		//		datasets: [{
		//		data: [feature.properties.City_Size,feature.properties.Market_Potential,feature.properties.Urban_Rate,feature.properties.Local_Dominance]
		//			}]
		//	}});
		
		////////////////////////////////////////	
				
				
				// 지도 데이터 팝업 
				
				 layer.bindPopup(   
					'<p class="tableLocation">'+ feature.properties.Names +'<br>'+ feature.properties.ISO3 + '</p>'+
					'<table id="popup">' +
			       		'<tr>'+
			       			'<td class="tabletitle">Variables</td>'+
			       			'<td class="tabletitle">Value</td>'+ 
			       			'<td class="tabletitle">Variables</td>'+
			       			'<td class="tabletitle">Value</td>'+ 
			       		'</tr>'+
			       		'<tr>'+
			       			'<td class="tabledata">City Size</td>'+
			       			'<td class="tabledata">'+(feature.properties.City_Size)+'</td>'+
			       			'<td class="tabledata">ID</td>'+
			       			'<td class="tabledata">'+(feature.properties.Agglomeration_ID)+'</td>'+
			       		'</tr>'+
			       		'<tr>'+
			       			'<td class="tabledata">Market Potential</td>'+
			       			'<td class="tabledata">'+(feature.properties.Market_Potential)+'</td>'+
			       			'<td class="tabledata">Country</td>'+
			       			'<td class="tabledata">'+feature.properties.ISO3+'</td>'+
			       		'</tr>'+
			       		'<tr>'+
			       			'<td class="tabledata">Urbanisation Level</td>'+
			       			'<td class="tabledata">'+(feature.properties.Urban_Rate).toFixed(2)+'</td>'+
			       			'<td class="tabledata">Lon</td>'+
			       			'<td class="tabledata">'+(feature.properties.Lon).toFixed(2)+'</td>'+
			       		'</tr>'+
			       		'<tr>'+
			       			'<td class="tabledata">Local Dominance</td>'+
			       			'<td class="tabledata">'+(feature.properties.Local_Dominance).toFixed(2)+'</td>'+
			       			'<td class="tabledata">Lat</td>'+
			       			'<td class="tabledata">'+(feature.properties.Lat).toFixed(2)+'</td>'+
			       		'</tr>'+
			       		'<tr>'+
			       			'<td class="tabledata">Growth Rate</td>'+
			       			'<td class="tabledata">'+(feature.properties.GrowthRate).toFixed(2)+'</td>'+
			       			'<td class="tabledata">City Group</td>'+
			       			'<td class="tabledata">'+(feature.properties.Cluster_group)+'</td>'+
			       		'</tr>' +
			       		'</table>'
				);
			}
		} 
	}); //getJSON.korea 끝 
}

$('#closeBoard').click(function() {
			$('#dashboard').hide();
		});
