// 기본 세팅 
	$(document).ready(function() {
  		$('#size_overall').prop("checked", true);
		$('#categoryAll').prop("checked", true);
	}); // document 끝 

// 지도 
var map = L.map('map').setView([6.5486547,3.2570718], 5);
  
// 데이터 파일 로딩 
function readfile (filename) {
	$.getJSON("./data/SWAC.geojson", function(statesData) {
 
	var yearAmap = statesData; // 지도데이터 저장 
  
		//$.getJSON(filename, function(maploc) { 
		//var lengthFirst = maploc.location.length; 
		//var lengthSecond =  yearAmap.features.length;  

		// 지도 지역 geojson에 데이터 json 파일 추가. 기준 : 행정지역코드

		//	for(var i=0 ; i<lengthFirst; i++) { 
		//		for(var j=0; j<lengthSecond; j++) {
			//		if( maploc.location[i].code == yearAmap.features[j].properties.A1) {
				//		yearAmap.features[j].properties.grand =  maploc.location[i].grand; 
					//	yearAmap.features[j].properties.location =  maploc.location[i].location; 
					//	yearAmap.features[j].properties.crime =  maploc.location[i].crime; 
					//	yearAmap.features[j].properties.murder =  maploc.location[i].murder; 
					//	yearAmap.features[j].properties.murder2 =  maploc.location[i].murder2; 
					//	yearAmap.features[j].properties.burglar =  maploc.location[i].burglar; 
					//	yearAmap.features[j].properties.robbery =  maploc.location[i].robbery; 
					//	yearAmap.features[j].properties.violence =  maploc.location[i].violence; 
					//	yearAmap.features[j].properties.sexual =  maploc.location[i].sexual; 
					//	yearAmap.features[j].properties.emptyA =  maploc.location[i].emptyA; 
					//	yearAmap.features[j].properties.emptyB =  maploc.location[i].emptyB; 
					//	yearAmap.features[j].properties.emptyC =  maploc.location[i].emptyC; 
					//	yearAmap.features[j].properties.emptyD =  maploc.location[i].emptyD;  
					//}
				//}
			//} // for 문 끝
			mapDraw(yearAmap); 
	//}); //getJSON 끝 

	// 지도 
	function mapDraw(event) {  

			var basemap = L.tileLayer('https://api.mapbox.com/styles/v1/ssong3819/ciyv34bt8002e2srzq0wi7lv4/tiles/256/{z}/{x}/{y}?access_token=pk.eyJ1Ijoic3NvbmczODE5IiwiYSI6ImNpamk4Zng5YjAydXR0eWx0eDAzeGcxYzMifQ.jeHvWzN-KshZRoPO4mc6qA', {
					minZoom: 3,
					maxZoom: 11
					}).addTo(map); 
		
			
			// 범죄별 지도 한 장 = 레이어 한 장. 범죄 항목을 선택할 때마다 레이어를 hide/show
			
			
			var City_Size =  L.geoJson(event, {  style: style, onEachFeature: onEachFeature });  
			var City_Size_cluster =  new L.MarkerClusterGroup({showCoverageOnHover: false});  
			var Market_Potential =  L.geoJson(event, {style: style2, onEachFeature: onEachFeature});  
			var Local_Dominance =  L.geoJson(event, {style: style3, onEachFeature: onEachFeature});  
			var Urban_Rate =  L.geoJson(event, {style: style4, onEachFeature: onEachFeature});  
			var violence =  L.geoJson(event, {style: style5, onEachFeature: onEachFeature});  
			var sexual =  L.geoJson(event, {style: style6, onEachFeature: onEachFeature});  
			var emptyA =  L.geoJson(event, {style: style7, onEachFeature: onEachFeature});  
			var emptyB =  L.geoJson(event, {style: style8, onEachFeature: onEachFeature});  
			var emptyC =  L.geoJson(event, {style: style9, onEachFeature: onEachFeature});  
			var emptyD =  L.geoJson(event, {style: style10, onEachFeature: onEachFeature});  

			// 기본 범죄 지도 
			City_Size_cluster.addLayer(City_Size);
			City_Size_cluster.addTo(map);
			// 지도 지역 라벨 
		 
			// 각 범죄 항목을 선택하면 지도 변경
			$('input:radio[name="crimeSelected"]').change(function(){
				
				// 전체 레이어를 지우고 다시 추가 
				function deleteme ( ) {
					map.removeLayer(crime);          map.removeLayer(robbery);
					map.removeLayer(murder);       map.removeLayer(violence);
					map.removeLayer(burglar);          map.removeLayer(sexual);
					map.removeLayer(emptyA);       map.removeLayer(emptyB);
					map.removeLayer(emptyC);          map.removeLayer(emptyD);
				}
 
				if($('input:radio[name="crimeSelected"]:input[value=crime]').is(":checked"))  {  deleteme(); map.addLayer(crime) }  
				if($('input:radio[name="crimeSelected"]:input[value=murder]').is(":checked"))  {  deleteme(); map.addLayer(murder) }  
				if($('input:radio[name="crimeSelected"]:input[value=burglar]').is(":checked"))  {  deleteme(); map.addLayer(burglar) }  
			                 if($('input:radio[name="crimeSelected"]:input[value=robbery]').is(":checked"))  {  deleteme(); map.addLayer(robbery) }  
				if($('input:radio[name="crimeSelected"]:input[value=violence]').is(":checked"))  {  deleteme(); map.addLayer(violence) }  
				if($('input:radio[name="crimeSelected"]:input[value=sexual]').is(":checked"))  {  deleteme(); map.addLayer(sexual) }  
				if($('input:radio[name="crimeSelected"]:input[value=emptyA]').is(":checked"))  {  deleteme(); map.addLayer(emptyA) }  
			                 if($('input:radio[name="crimeSelected"]:input[value=emptyB]').is(":checked"))  {  deleteme(); map.addLayer(emptyB) }  
				if($('input:radio[name="crimeSelected"]:input[value=emptyC]').is(":checked"))  {  deleteme(); map.addLayer(emptyC) }  
				if($('input:radio[name="crimeSelected"]:input[value=emptyD]').is(":checked"))  {  deleteme(); map.addLayer(emptyD) }  
			});


			
			map.scrollWheelZoom.disable(); 
			//map.dragging.disable(); // 드래그 금지
			//map.zoomControl.remove(); // zoom 버튼 삭제 
  
  			// 지도 컬러 범위  ===========================================================================
			function ctA(d) {
			    return d > 217.7 ? '#b3282f' :
			           d > 140.13  ? '#ee2537' :
			           d > 103.7  ? '#fe663b' :
			           d > 72.5  ? '#f9c63f' :
			           d > 33.0   ? '#e5d948' : 
			                      '#eee';
			} // 5대 강력 범죄 전체 

			function ctB(d) {
			    return d > 0.5113 ? '#b3282f' :
			           d > 0.2770  ? '#ee2537' :
			           d > 0.1585  ? '#fe663b' :
			           d > 0.4753  ? '#f9c63f' :
			           d > 0.0001   ? '#e5d948' : 
			                      '#eee';
			} //  살인  

			
			function ctC(d) {
			    return d > 0.8906 ? '#b3282f' :
			           d > 0.5539  ? '#ee2537' :
			           d > 0.3079  ? '#fe663b' :
			           d > 0.1188  ? '#f9c63f' :
			           d > 0 ? '#e5d948' : 
			                      '#eee';
			} // 만명당 강도 
			 
			function ctD(d) {
			    return d > 87.1689 ? '#b3282f' :
			           d > 51.4514  ? '#ee2537' :
			           d > 35.7266  ? '#fe663b' :
			           d > 24.101  ? '#f9c63f' :
			           d > 0   ? '#e5d948' : 
			                      '#eee';
			} // 만명당 절도 

			function ctE(d) {
			    return d > 119.3222 ? '#b3282f' :
			           d > 72.2058 ? '#ee2537' :
			           d > 53.3465  ? '#fe663b' :
			           d > 38.4362  ? '#f9c63f' :
			           d > 0  ? '#e5d948' : 
			                      '#eee';
			} // 만명당 폭력 

			function ctF(d) {
			    return d > 14.1567 ? '#b3282f' :
			           d > 8.1860  ? '#ee2537' :
			           d > 5.1655  ? '#fe663b' :
			           d > 3.3319  ? '#f9c63f' :
			           d > 0.00   ? '#e5d948' : 
			                      '#eee';
			} // 만명당 성폭력 

			function ctG(d) {
			    return d > 7.30 ? '#b3282f' :
			           d > 6.11  ? '#ee2537' :
			           d > 5.13  ? '#fe663b' :
			           d > 4.23  ? '#f9c63f' :
			           d > 3.21   ? '#e5d948' : 
			                      '#eee';
			} // 경찰 출동시간  

			function ctH(d) {
			    return d > 82.4 ? '#b3282f' :
			           d > 79.20  ? '#ee2537' :
			           d > 76.70  ? '#fe663b' :
			           d > 74.50  ? '#f9c63f' :
			           d > 0.00   ? '#e5d948' : 
			                      '#eee';
			} //  치안만족도 

			function ctI(d) {
			    return d > 112.335 ? '#b3282f' :
			           d > 69.3765  ? '#ee2537' :
			           d > 47.2129  ? '#fe663b' :
			           d > 30.0794  ? '#f9c63f' :
			           d > 0.00   ? '#e5d948' : 
			                      '#eee';
			} // CCTV  

			function ctJ(d) {
			    return d > 713.8435 ? '#b3282f' :
			           d > 545.1424  ? '#ee2537' :
			           d > 415.4920  ? '#fe663b' :
			           d > 292.5592  ? '#f9c63f' :
			           d > 0.00   ? '#e5d948' : 
			                      '#eee';
			} // 1인당 담당인구 
 		
 			// 지도 컬러 함수 ===========================================================================
			function style (feature) { 
				return {     fillColor:  ctA(feature.properties.City_Size), color: 'white',  fillOpacity: 0.5, dashArray: '3', weight:2,  className: (feature.properties.Cluster_group)  }
			}

			function style2 (feature) { 
				return {     fillColor:  ctB(feature.properties.Market_Potential),  color: 'white',  fillOpacity: 0.5, dashArray: '3', weight:2, className: (feature.properties.Cluster_group)    }
			} 

			function style3 (feature) { 
				return {       fillColor:  ctC(feature.properties.Local_Dominance),  color: 'white',  fillOpacity: 0.5, dashArray: '3', weight:2, className: (feature.properties.Cluster_group)   }
		 	} 

		 	function style4 (feature) { 
				return {       fillColor:  ctD(feature.properties.Urban_Rate),  color: 'white',  fillOpacity: 0.5, dashArray: '3', weight:2, className: (feature.properties.Cluster_group)       }
		 	} 

		 	function style5 (feature) { 
				return {       fillColor:  ctE(feature.properties.violence),  color: 'white',  fillOpacity: 0.5, dashArray: '3', weight:2, className: (feature.properties.Cluster_group)      }
		 	} 

		 	function style6 (feature) { 
				return {       fillColor:  ctF(feature.properties.sexual),  color: 'white',  fillOpacity: 0.5, dashArray: '3', weight:2, className: (feature.properties.Cluster_group)       }
		 	} 

		 	function style7 (feature) { 
				return {       fillColor:  ctG(feature.properties.emptyA),  color: 'white',  fillOpacity: 0.5, dashArray: '3', weight:2, className: (feature.properties.Cluster_group)      }
		 	} 

		 	function style8 (feature) { 
				return {       fillColor:  ctH(feature.properties.emptyB),  color: 'white',  fillOpacity: 0.5, dashArray: '3', weight:2, className: (feature.properties.Cluster_group)       }
		 	} 

		 	function style9 (feature) { 
				return {       fillColor:  ctI(feature.properties.emptyC),  color: 'white',  fillOpacity: 0.5, dashArray: '3', weight:2, className: (feature.properties.Cluster_group)       }
		 	} 

		 	function style10 (feature) { 
				return {       fillColor:  ctJ(feature.properties.emptyD),  color: 'white',  fillOpacity: 0.5, dashArray: '3', weight:2, className: (feature.properties.Cluster_group)       }
		 	} 
 

		 	// 마우스를 올리거나 터치했을 때 이벤트 
			function highlightFeature(e) {
				var layer = e.target;

				layer.setStyle({ 
					fillOpacity: 0.8
				});

				if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) {
					layer.bringToFront();
				} 

				this.openPopup();
			}
 
			// 원래 상태로 돌아갔을 때 이벤트 
			function resetHighlight(e) {
				var layer = e.target;

				layer.setStyle({ 
					fillOpacity: 0.5
				}); 

				this.closePopup();
			}

			// 지도 인터랙션 함수. 팝업 / 지도 라벨 등 
			function onEachFeature(feature, layer) {
				layer.on({
					mouseover: highlightFeature,
					mouseout: resetHighlight 
				}); 

				 

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
