$(document).ready(
    function() {  
	var trackindex = getTrackIndex(); // cherche en ajax la liste des traces à afficher
    try {
	     var bounds = new OpenLayers.Bounds(trackindex["minlon"],trackindex["minlat"],trackindex["maxlon"],trackindex["maxlat"]);
    }
    catch(e) {
         var bounds =  new OpenLayers.Bounds(-2,42,4,51);
        }
	setMainMap('ol',bounds,['mapnik']);
	var tracks = [];
	for (var i in trackindex){
	    tracks.push(trackindex[i]);
	}
	addMarkerTracks(mainmap,tracks);
	
	mainmap.events.on({ "moveend": function (e) {
	    var bnds =  mainmap.getExtent().transform(mainmap.getProjectionObject(), geographic);
	    getTracksFromBounds(bnds);
	    getTracksNearby(0);
	    // var maxbnds = mainmap.getMaxExtent().transform(mainmap.getProjectionObject(), geographic);
	}
});



   mainmap.zoomToExtent(bounds.transform(geographic, mainmap.getProjectionObject()));
   getTracksNearby(0);

   // afficher directement une nouvelle trace dans la carte en cours

 });
