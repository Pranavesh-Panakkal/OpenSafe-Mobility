# Title     : Validation plot template
# Created by: Pranavesh Panakkal
# Created on: 9/6/2021
# Version   :
# Notes     :
""""""
from jinja2 import Template

# TEMPLATE = Template("""\
# <!DOCTYPE html>
# <html lang="en">
#     <head>
#         <meta charset="utf-8">
#         <title>OpenSafe Mobility Validation</title>
#         {{ resources }}
#         <link rel="stylesheet" href="tailwind_style.css">
#     </head>
#     <body>
#         <div class="w-full min-h-screen p-10">
#             <header class="pb-10">
#                 <a href="../index.html" class="text-gray-700 text-2xl font-semibold">OpenSafe Moblility</a>
#                 <h3 class="text-base font-semibold">Dashboard</h3>
#             </header>
#
#             <div class="flex flex-wrap justify-center grid lg:grid-cols-2 gap-10">
#                 <div class="flex flex-col bg-white rounded-lg shadow-md w-full overflow-hidden">
#                     <div align="center">
#                     {{ plot_div.map }}
#                     </div>
#                     <span class="font-bold">The most recent 3-hour rainfall spatial distribution over the Brays Bayou watershed</span>
#                     <span class="block text-gray-500 text-sm">Rainfall distribution over the study region. Hover over the map for more information. Regions without data are mareked in grey.</span>
#                 </div>
#
#                 <div class="flex flex-col bg-white rounded-lg shadow-md w-full overflow-hidden">
#                     <div align="center">
#                     {{ plot_div.rainfall_time_series }}
#                     </div>
#                     <span class="font-bold">Average cumulative rainfall time history</span>
#                     <span class="block text-gray-500 text-sm">Average distribution of rainfall overtime.</span>
#                 </div>
#
#                 <div class="flex flex-col bg-white rounded-lg shadow-md w-full overflow-hidden">
#                  <div align="center">
#                     {{ plot_div.trigger_criteria }}
#                 </div>
#                     <span class="font-bold">Rainfall trigger threshold</span>
#                     <span class="block text-gray-500 text-sm">OpenSafe Mobility will trigger model run once the maximum observed rainfall in any sub-region exceed the NOAA Atlas-15 5-year rainfall (red line).</span>
#                 </div>
#
#                 <div class="flex flex-col bg-white rounded-lg shadow-md w-full overflow-hidden">
#
#                     <div class="grid grid-cols-2">
#                         <div align="center">
#                         {{ plot_div.gage_1 }}
#                         </div>
#                         <div align="center">
#                         {{ plot_div.gage_3 }}
#                         </div>
#                     </div>
#                     <span class="font-bold">Real-time sate reading from USGS</span>
#                     <span class="block text-gray-500 text-sm">Gage level from two locations in the watershed.</span>
#                 </div>
#             </div>
#
#         </div>
#     {{ plot_script }}
#     </body>
# </html>
# """)


def get_jinga_template(config):
    """Return the Jinga template"""
    fig_1_title = config.website.validation_dashboard.figure_labels.figure_1.main_title
    fig_1_main = config.website.validation_dashboard.figure_labels.figure_1.description
    fig_1_source = config.website.validation_dashboard.figure_labels.figure_1.sources
    fig_1_source_ref = (
        config.website.validation_dashboard.figure_labels.figure_1.sources_ref
    )

    fig_2_title = config.website.validation_dashboard.figure_labels.figure_2.main_title
    fig_2_main = config.website.validation_dashboard.figure_labels.figure_2.description
    fig_2_source = config.website.validation_dashboard.figure_labels.figure_2.sources
    fig_2_source_ref = (
        config.website.validation_dashboard.figure_labels.figure_2.sources_ref
    )

    fig_3_title = config.website.validation_dashboard.figure_labels.figure_3.main_title
    fig_3_main = config.website.validation_dashboard.figure_labels.figure_3.description
    fig_3_source = config.website.validation_dashboard.figure_labels.figure_3.sources
    fig_3_source_ref = (
        config.website.validation_dashboard.figure_labels.figure_3.sources_ref
    )

    fig_4_title = config.website.validation_dashboard.figure_labels.figure_4.main_title
    fig_4_main = config.website.validation_dashboard.figure_labels.figure_4.description
    fig_4_source = config.website.validation_dashboard.figure_labels.figure_4.sources
    fig_4_source_ref = (
        config.website.validation_dashboard.figure_labels.figure_4.sources_ref
    )

    TEMPLATE = Template(
        f"""
       <!DOCTYPE html>
       <html lang="en">
           <head>
               <meta charset="utf-8">
               <title>OpenSafe Mobility Validation</title>
               {"{{"} resources {"}}"}
               <link rel="stylesheet" href="tailwind_style.css">
           </head>
           <body>
               <div class="w-full min-h-screen p-10">
                   <header class="pb-10">
                       <a href="../index.html" class="text-gray-700 text-2xl font-semibold">OpenSafe Mobility</a>
                       <h3 class="text-base font-semibold">Dashboard</h3>
                   </header>

                   <div class="flex flex-wrap justify-center grid lg:grid-cols-2 gap-10">
                       <div class="flex flex-col bg-white rounded-lg shadow-md w-full overflow-hidden">
                           <div align="center">
                           {"{{"} plot_div.map {"}}"}
                           </div>
                           
                           <div class="p-4 flex-1 flex flex-col" style="">
                                <h3 class="mb-4 text-2xl">{fig_1_title}</h3>
                            <div class="mb-4 text-grey-darker text-sm flex-1">
                              <p>{fig_1_main}</p>
                            </div>
                            <a href={fig_1_source_ref} class="border-t border-grey-light pt-2 text-xs text-grey hover:text-red uppercase no-underline tracking-wide" style="">{fig_1_source}</a>
                          </div>

                       </div>

                       <div class="flex flex-col bg-white rounded-lg shadow-md w-full overflow-hidden">
                           <div align="center">
                           {"{{"} plot_div.rainfall_time_series {"}}"}
                           </div>
                           
                           <div class="p-4 flex-1 flex flex-col" style="">
                                <h3 class="mb-4 text-2xl">{fig_2_title}</h3>
                            <div class="mb-4 text-grey-darker text-sm flex-1">
                              <p>{fig_2_main}</p>
                            </div>
                            <a href={fig_2_source_ref} class="border-t border-grey-light pt-2 text-xs text-grey hover:text-red uppercase no-underline tracking-wide" style="">{fig_2_source}</a>
                          </div>
             
                       </div>

                       <div class="flex flex-col bg-white rounded-lg shadow-md w-full overflow-hidden">
                        <div align="center">
                           {"{{"} plot_div.trigger_criteria {"}}"}
                       </div>
                       
                           <div class="p-4 flex-1 flex flex-col" style="">
                                <h3 class="mb-4 text-2xl">{fig_3_title}</h3>
                            <div class="mb-4 text-grey-darker text-sm flex-1">
                              <p>{fig_3_main}</p>
                            </div>
                            <a href={fig_3_source_ref} class="border-t border-grey-light pt-2 text-xs text-grey hover:text-red uppercase no-underline tracking-wide" style="">{fig_3_source}</a>
                          </div>
                          
                       </div>

                       <div class="flex flex-col bg-white rounded-lg shadow-md w-full overflow-hidden">

                           <div class="grid grid-cols-2">
                               <div align="center">
                               {"{{"} plot_div.gage_1 {"}}"}
                               </div>
                               <div align="center">
                               {"{{"} plot_div.gage_3 {"}}"}
                               </div>
                           </div>
                           
                           <div class="p-4 flex-1 flex flex-col" style="">
                                <h3 class="mb-4 text-2xl">{fig_4_title}</h3>
                            <div class="mb-4 text-grey-darker text-sm flex-1">
                              <p>{fig_4_main}</p>
                            </div>
                            <a href={fig_4_source_ref} class="border-t border-grey-light pt-2 text-xs text-grey hover:text-red uppercase no-underline tracking-wide" style="">{fig_4_source}</a>
                          </div>
                          
                       </div>
                   </div>

               </div>
           {"{{"} plot_script {"}}"}
           </body>
       </html>
       """
    )
    return TEMPLATE
