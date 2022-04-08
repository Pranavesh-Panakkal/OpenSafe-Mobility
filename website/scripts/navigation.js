// Navigation border click





const collapsedClass = "nav--collapsed";
const lsKey = "navCollapsed";
const nav = document.querySelector(".nav");
const navBorder = nav.querySelector(".nav__border");
if (localStorage.getItem(lsKey) === "true") {
  nav.classList.add(collapsedClass);
}

//   When the nav border is clicked, collapse the navigation bar
navBorder.addEventListener("click", () => {
  nav.classList.toggle(collapsedClass);
  // Store the state of the navigation bar. This will be done on the local browser cache
  localStorage.setItem(lsKey, nav.classList.contains(collapsedClass));
});

const logo_button = nav.querySelector("#logo");
logo_button.addEventListener("click", () => {
  nav.classList.toggle(collapsedClass);
  // Store the state of the navigation bar. This will be done on the local browser cache
  localStorage.setItem(lsKey, nav.classList.contains(collapsedClass));
});

// reload_visibility();

// // Loading Flood Inundation
// // const flood_depth_visible = "visible";
// // Where to toggle the active button tag
// // Link to the button

// Active tag for active layers
const layer_status_class = "layer_active";

// Class name of the buttons; we will be appeding the layer active status to this layer
const layer_status_flood_depth = document.querySelector(".flood_depth");
const layer_status_road_condition = document.querySelector(".road_condition");
const layer_status_access_to_fire = document.querySelector(".access_to_fire");
const layer_status_access_to_hospitals = document.querySelector(".access_to_hospitals");
const layer_status_access_to_dialysis = document.querySelector(".access_to_dialysis");

// Adding tags to legend
const legend_fire = document.querySelector(".legend_fire_stations");
const legend_hospitals = document.querySelector(".legend_hospitals");
const legend_dialysis_centers = document.querySelector(".legend_dialysis_center");
const legend_road_condition = document.querySelector(".legend_flooded_roads");
const legend_water_depth = document.querySelector(".legend_water_depth");

// const flood_depth_button = nav.querySelector("#flood_depth_button");
// const road_condition_button = nav.querySelector("#road_condition_button");
// const access_to_fire_button = nav.querySelector("#access_to_fire_button");
// const access_to_hospitals_button = nav.querySelector("#access_to_hospitals_button");
// const access_to_dialysis_centers_button = nav.querySelector("#access_to_dialysis_centers_button");

// 'Inundation Depth', 

// window.onload = function reload_visibility() {
//   const toggleableLayerIds = ['Flooded roads', 'Accessibility Measures (Fire Stations)'];

//   for (i = 0; i < toggleableLayerIds.length; i++) {
//     var layer_name = toggleableLayerIds[i];

//     alert(layer_name)
//     alert(localStorage.getItem(layer_name))

//     if (localStorage.getItem(layer_name) !== null) {
//       alert("here")
//       if (localStorage.getItem(layer_name)==='true') {
//         alert("true here")
//         show_layers([layer_name])
//         // show_layers([layer_name])
//       } else {
//         alert("false here")
//         hide_layers([layer_name])
//       }
//     };
//   };
// };
// Managing local storage
// const Key_flood_depth = "flood_layer_active";
// const Key_road_condition = "road_condition_layer_active";
// const Key_access_to_fire= "access_to_fire_layer_active";
// const Key_flood_depth = "flood_layer_active";
// const Key_flood_depth = "flood_layer_active";
// if (localStorage.getItem(Key_flood_depth) === "true") {
//   layer_status_flood_depth.classList.setItem(layer_status_class);
// }


// if (localStorage.getItem(Key_flood_depth) === "true") {
//   layer_status_flood_depth.classList.setItem(layer_status_class);
// } else {
//   layer_status_flood_depth.classList.toggle(layer_status_class);
// }

// if (localStorage.getItem(Key_road_condition) === "true") {
//   alert("Road codition was true")
//   // layer_status_road_condition.classList.setItem(layer_status_class);
// };
// localStorage.setItem(local_key_flood_depth_visible, layer_status_flood_depth.classList.contains(collapsedClass));

// Loading Flooded roads
flood_depth_button.addEventListener("click", () => {
  // Toggle staus
  layer_status_flood_depth.classList.toggle(layer_status_class)
  legend_water_depth.classList.toggle(layer_status_class)
  // Manage layer visibility
  manage_visibility(layer_status_flood_depth.classList.contains(layer_status_class), 'Inundation Depth')
});


// Loading Flooded roads
road_condition_button.addEventListener("click", () => {
  // Toggle staus
  layer_status_road_condition.classList.toggle(layer_status_class)
  legend_road_condition.classList.toggle(layer_status_class)
  // Manage layer visibility
  manage_visibility(layer_status_road_condition.classList.contains(layer_status_class), 'Flooded roads')
});


// Loading Fire stations
access_to_fire_button.addEventListener("click", () => {
  // Toggle staus
  layer_status_access_to_fire.classList.toggle(layer_status_class)
  // legend_fire.classList.toggle(layer_status_class)
  legend_fire.classList.toggle(layer_status_class)
  // Manage layer visibility
  manage_visibility(layer_status_access_to_fire.classList.contains(layer_status_class), 'Accessibility Measures (Fire Stations)')
  // Switch off the location of fire stations
  manage_visibility(layer_status_access_to_fire.classList.contains(layer_status_class), 'Location of fire stations')
});



// Loading Hospitals
access_to_hospitals_button.addEventListener("click", () => {
  // Toggle staus
  layer_status_access_to_hospitals.classList.toggle(layer_status_class)
  // Toggle legend
  legend_hospitals.classList.toggle(layer_status_class)
  // Manage layer visibility
  manage_visibility(layer_status_access_to_hospitals.classList.contains(layer_status_class), 'Accessibility Measures (Hospitals)')
  // Switch off the locations of hospitals
  manage_visibility(layer_status_access_to_hospitals.classList.contains(layer_status_class), 'Location of Hospitals')
});



// Loading Dialysis Centers
access_to_dialysis_centers_button.addEventListener("click", () => {
  // Toggle staus
  layer_status_access_to_dialysis.classList.toggle(layer_status_class)
  // Toggle legend
  legend_dialysis_centers.classList.toggle(layer_status_class)

  // alert("Button pressed")
  // Manage layer visibility
  manage_visibility(layer_status_access_to_dialysis.classList.contains(layer_status_class), 'Accessibility Measures (Dialysis Centers)')
  // Switch off the locations of dialysis centers
  manage_visibility(layer_status_access_to_dialysis.classList.contains(layer_status_class), 'Location of Dialysis Centers')
});


function toggle_visibility(layer_name) {
  // Get layer condition
  const visibility = map.getLayoutProperty(layer_name, 'visibility');
  // Toggle visibility
  if (visibility === 'visible') {
    hide_layers([layer_name]);
  } else {
    show_layers([layer_name]);
  }
};

function manage_visibility(current_status, layer_name) {
  if (current_status) {
    show_layers([layer_name])
    localStorage.setItem(layer_name, true)
  } else {
    hide_layers([layer_name])
    localStorage.setItem(layer_name, false)
  };
};


// window.onload = reload_visibility();

// function reload_visibility() {
//   const toggleableLayerIds = ['Inundation Depth', 'Flooded roads', 'Accessibility Measures (Fire Stations)'];
//   alert("herea")
//   for (i = 0; i < toggleableLayerIds.length; i++) {
//     var item_id = toggleableLayerIds[i];
//     if (localStorage.getItem(item_id) !== null) {
//       manage_visibility(localStorage.getItem(item_id), item_id)
//     };
// };


//   for (const id of toggleableLayerIds) {
//     alert(id)
//     // Get the status of item
//     if (localStorage.getItem(id) !== null) {
//       manage_visibility(localStorage.getItem(id), id)
//     };
//   }; 
// };
// Popup
