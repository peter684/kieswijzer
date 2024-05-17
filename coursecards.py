import streamlit as st
import streamlit.components.v1 as components
from streamlit_extras.stylable_container import stylable_container

import constants as cs


# from constants import learning_lines

def pill_html(color):
    return f'''
        <div style="
            float:left; 
            width:15px;
            height:3px; 
            margin:1px; 
            border: solid {color}; 
            background-color: {color}; 
            border-radius: 5px; 
            padding: 1px;">
        </div>
          '''


def pill_box(colors):
    pill_html = ""
    for ll in cs.learning_lines:
        course_color = ll["color"]
        col = "rgba(255,255,255,0)"
        for c in colors:
            if course_color == c:
                col = course_color
                continue
        pill_html += f"""
            <div style="
                float:left; 
                width:15px;
                height:3px; 
                margin:1px; 
                border: solid {col}; 
                background-color: {col}; 
                border-radius: 5px; 
                padding: 1px;">
            </div>"""
    return pill_html


def pills_legend(learning_lines=None, font=None, font_size=None):
    ff = font if font is not None else 'Source Sans Pro, sans-serif'
    fs = font_size if font_size is not None else "15px"
    learning_lines = learning_lines if learning_lines is not None else cs.learning_lines
    legend_html = f'''
    <table style="
        font-family:{ff};
        font-size:{fs};
        color: #31333F;
    ">
    
    '''
    for ll in learning_lines:
        course_name = ll["name"]
        course_color = ll["color"]
        legend_html += f'''
                  <tr>
                    <td>
                        {pill_html(course_color)}
                    </td>
                    <td>{course_name}</td>
                  </tr>'''
    legend_html += '</table>'
    legend_html.replace('&', '&amp;')
    components.html(legend_html, height=175)


def course_tile(pill_colors, label, theme, tile_id, height=80, width=175, fontsize=12):
    tile_container_style = f"""
        {{  
            overflow:hidden; 
            border:3px solid {theme["tile"]["bordercolor"]}; 
            background-color:{theme["tile"]["backgroundcolor"]}; 
            border-radius:8px; 
            padding:3px;
            height:{height};
            width:{width};
        }}
    """
    key = f"tile_container{tile_id}"
    key = key.replace('(', '_')
    key = key.replace(')', '_')
    with stylable_container(key=key, css_styles=tile_container_style):
        # draw either colored or transparant pill
        # draw course info
        tile_html = f"""
            {pill_box(pill_colors)}
            <div>
                <p style="
                    font-family:Tahoma, Geneva, sans-serif;
                    font-size:{fontsize}px;
                    color: {theme["tile"]["fontcolor"]};
                "><br>
                  {label}
                </p>
            </div>
            """
        # render html
        components.html(tile_html, height=min(70, height - 20), width=width - 20)


def course_card_buttons(pill_colors, label, theme, course_id, width=250, buttons=None):
    wrapping_container_padding = 5
    wrapping_container_border = 5
    tile_container_padding = 3
    tile_container_border = 3
    tile_container_width = 1.0 * (width - 2 * (
            wrapping_container_padding + wrapping_container_border + tile_container_padding + tile_container_border))
    wrapping_container_style = f"""
        {{
            background-color:{theme["container"]["backgroundcolor"]};
            border: {wrapping_container_border}px solid {theme["container"]["bordercolor"]};
            border-radius:10px;
            padding:{wrapping_container_padding}px;
            width:{width - 2 * wrapping_container_border - 2 * wrapping_container_padding}px;
            box-shadow: 0 8px 16px 0 rgba(0,0,0,0.2), 0 6px 20px 0 rgba(0,0,0,0.19);
        }}
    """

    button_style = f"""
        button{{
            border: 2px solid {theme["button"]["bordercolor"]};
            background-color: {theme["button"]["backgroundcolor"]}; 
            color:{theme["button"]["color"]}; 
            border-radius:5px; 
            margin:5px;
            padding:5px;
        }}
    """
    key = f"wrapping_container{course_id}"
    key = key.replace('(', '_')
    key = key.replace(')', '_')
    with stylable_container(key=key, css_styles=wrapping_container_style):
        course_tile(
            pill_colors=pill_colors,
            label=label,
            theme=theme,
            tile_id=course_id,
            height=125,
            width=int(tile_container_width),
            fontsize=12,
        )
        if buttons is not None:
            cols = st.columns(len(buttons))
            for index, col in enumerate(cols):
                btn_label = buttons[index]["label"]
                btn_key = f'btn_{btn_label}_{course_id}'
                btn_key = btn_key.replace('(', '_')
                btn_key = btn_key.replace(')', '_')
                btn_function = buttons[index]["func"]
                ctr_key = f"edit_container{course_id}"
                ctr_key = ctr_key.replace('(', '_')
                ctr_key = ctr_key.replace(')', '_')
                with col:
                    with stylable_container(key=ctr_key, css_styles=button_style):
                        st.button(
                            label=btn_label, key=btn_key, on_click=btn_function, args=[course_id]
                        )
