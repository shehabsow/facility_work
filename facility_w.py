import streamlit as st
import pandas as pd
import os
from datetime import datetime
from PIL import Image
import pytz
import io
from io import BytesIO
# إعداد تكوين الصفحة في Streamlit
st.set_page_config(
    layout="wide",
    page_title='facility_w',
    page_icon='🪙')

egypt_tz = pytz.timezone('Africa/Cairo')

# تحميل البيانات مرة واحدة باستخدام التخزين المؤقت

def load_checklist_data():
    if os.path.exists('checklist_records.xlsx'):
        df = pd.read_excel('checklist_records.xlsx', sheet_name='Sheet1', engine='openpyxl')
        for col in ['Date', 'Expected repair Date', 'Actual Repair Date']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce').dt.tz_localize(None)
        return df
    return pd.DataFrame(columns=[
        'event id', 'location', 'Element', 'Event Detector Name', 
        'Date', 'Rating', 'responsible person', 
        'Expected repair Date', 'Actual Repair Date', 'image path', 'comment'
    ])

def load_change_log():
    if os.path.exists('change_log.xlsx'):
        return pd.read_excel('change_log.xlsx', engine='openpyxl')
    return pd.DataFrame(columns=[
        'event id', 'modifier name', 'modification Date', 
        'modification type', 'new Date'
    ])
def to_excel(df):
    # تأكد من أن جميع الأعمدة التي تحتوي على تواريخ هي غير مزودة بمعلومات منطقة زمنية
    for col in df.select_dtypes(include=['datetime64[ns, UTC]', 'datetime64[ns]']):
        df[col] = df[col].apply(lambda x: x.tz_localize(None) if x.tzinfo else x)

    # إنشاء تدفق بيانات في الذاكرة
    output = BytesIO()

    # استخدام ExcelWriter لكتابة DataFrame إلى التدفق
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    
    return output.getvalue()


# حفظ البيانات في ملف CSV بشكل غير متزامن
def save_checklist_data(df):
    df.to_excel('checklist_records.xlsx', index=False, encoding='utf-8', engine='openpyxl')

def save_change_log(df):
    df.to_excel('change_log.xlsx', index=False, encoding='utf-8', engine='openpyxl')
# تهيئة بيانات الجلسة
if 'checklist_df' not in st.session_state:
    st.session_state.checklist_df = load_checklist_data()

if 'log_df' not in st.session_state:
    st.session_state.log_df = load_change_log()


checklist_items = {
    "Floors": [
        "Inspect floors for visible damage and stains"
    ],
    "Lights": [
        "Ensure all light fixtures are operational."
    ],
    "Electrical Outlets": [
        "Inspect all electrical outlets for visible damage",
        "Ensure all outlet covers are installed properly and not damaged.",
        "Verify all electrical outlets are labeled"
    ],
    "Doors": [
        "Inspect door for visible damage and paint chipping",
        "Check door hardware for proper operation (badge access, door handles)",
        "Ensure doors close and latch properly",
        "Inspect door seals"
    ],
    "Ceilings": [
        "Inspect ceilings for visible damage (including cracks, dings, dents, holes) and paint chipping",
        "Inspect ceiling penetrations around piping and ducting to ensure seals fully cover any gaps",
        "Sealing material is not dry or cracked"
    ],
    "Walls": [
        "Inspect walls for visible damage (including cracks, dings, dents, holes) and paint chipping",
        "Inspect all wall penetrations around piping to ensure seals fully cover any gaps and holes",
        "Sealing material is not dry or cracked."
    ],
    "Windows": [
        "Inspect windows for visible damage and cracks",
        "Inspect exterior window seals for cracking, holes, and gaps",
        "Inspect curtains for visible damage and standardize"
    ],
    "Visuals": [
        "Inspect visuals for visible damage or fading",
        "Ensure visuals are updated"
    ],
    "Fixtures and fittings": [
        "Inspect fixtures such as faucets, WC bowls, bathroom sinks, mirrors, etc.",
        "Inspect cafeteria & coffee corner fittings (coffee machines, kettles, Bain Marie, etc.)",
        "Inspect fixture and fitting condition for visible damage"
    ],
    "Furniture": [
        "Inspect movable office furniture, desks, chairs, sofas, tables, cabinets, etc.",
        "Inspect furniture condition for visible damage"
    ]
}

repair_personnel = ['Shehab Ayman', 'sameh', 'Kaleed', 'Yasser Hassan', 'Mohamed El masry',"Zeinab Mobarak"]

# دالة لتوليد رقم الحدث التالي
def get_next_event_id():
    if st.session_state.checklist_df.empty or 'event id' not in st.session_state.checklist_df.columns:
        return 'Work Order 1'

    event_ids = st.session_state.checklist_df['event id'].dropna().tolist()

    if not event_ids:
        return 'Work Order 1'

    try:
        last_id = event_ids[-1]
        if isinstance(last_id, str):
            last_num = int(last_id.split(' ')[-1])
        else:
            last_num = 0
    except (ValueError, IndexError):
        last_num = 0

    next_num = last_num + 1
    return f'Work Order {next_num}'

# الصفحة الرئيسية لتسجيل الأحداث
page = st.sidebar.radio('Select page', ['Event Logging', 'Work Shop Order', 'View Change Log', 'Clear data'])

if page == 'Event Logging':
    checklist_df = load_checklist_data()
    col1, col2 = st.columns([2, 0.75])
    with col1:
        st.markdown("""
                <h2 style='text-align: center; font-size: 40px; color: #A52A2A;'>
                    Facility Maintenance Checklist:
                </h2>
                """, unsafe_allow_html=True)
    with col2:
        search_keyword = st.session_state.get('search_keyword', '')
        search_keyword = st.text_input("Enter keyword to search:", search_keyword)
        search_button = st.button("Search")
        search_option = 'All Columns'
    
    def search_in_dataframe(df_Material, keyword, option):
        if option == 'All Columns':
            result = df_Material[df_Material.apply(lambda row: row.astype(str).str.contains(keyword, case=False).any(), axis=1)]
        else:
            result = df_Material[df_Material[option].astype(str).str.contains(keyword, case=False)]
        return result
    
    if st.session_state.get('refreshed', False):
        st.session_state.search_keyword = ''
        st.session_state.refreshed = False
    
    if search_button and search_keyword:
        st.session_state.search_keyword = search_keyword
        search_results = search_in_dataframe(st.session_state.checklist_df, search_keyword, search_option)
        st.write(f"Search results for '{search_keyword}'in{search_option}:")
        st.dataframe(search_results, width=1000, height=200)
    st.session_state.refreshed = True
    
    
    image_save_path = 'uploaded_images'
    os.makedirs(image_save_path, exist_ok=True)
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.subheader('Select Area:')
        locations = ['Admin indoor', 'QC lab & Sampling room', 'Processing', 'Receiving area & Reject room',
             'Technical corridor', 'Packaging', 'Warehouse', 'Utilities & Area Surround',
             'Outdoor & security gates', 'Electric rooms', 'Waste WTP & Incinerator',
             'Service Building & Garden Store', 'Pumps & Gas Rooms']

# عرض قائمة منسدلة لاختيار الموقع
        selected_location = st.selectbox("Select Location", locations)
        
        if selected_location:
            st.subheader(f'{selected_location} Checklist.')

    col1, col2 = st.columns([3, 3])

    with col1:

        for category, items in checklist_items.items():
            st.markdown(f"<h3 style='color:green; font-size:24px;'>{category}.</h3>", unsafe_allow_html=True)
    
            for item in items:
                st.markdown(f"<span style='color:blue; font-size:18px;'>* {item}</span>", unsafe_allow_html=True)
        
            col1a, col2a, col3a, col4a = st.columns([1, 2, 2, 2])
            Event_Detector_Name = col2a.text_input('Detector Name.', key=f"detector_name_{category}_{selected_location}")
            Rating = col1a.selectbox('Rating.', [0, 1, 2, 3, 'N/A'], key=f"Rating_{category}_{selected_location}")
            comment = col3a.text_input('Comment.', '', key=f"comment_{category}_{selected_location}")
            responsible_person = col4a.selectbox('Select Responsible Person.', [''] + repair_personnel, key=f"person_{category}_{selected_location}")
            uploaded_file = st.file_uploader(f"Upload Images {category}", type=["jpg", "jpeg", "png"], key=f"image_{category}_{selected_location}")
            
            if st.button(f'Add {category}', key=f"add_{category}_{selected_location}"):
                if Rating in [0, 'N/A']:
                    event_id = 'check'
                else:
                    event_id = get_next_event_id()
    
                image_path = ""
                if uploaded_file is not None:
                    try:
                        image = Image.open(uploaded_file)
                        if image.mode == "RGBA":
                            image = image.convert("RGB")
                        max_size = (800, 600)
                        image.thumbnail(max_size)
                        image_filename = os.path.join('uploaded_images', f"{event_id}.jpg") if event_id else os.path.join('uploaded_images', f"no_id_{uploaded_file.name}")
                        image.save(image_filename, optimize=True, quality=85)
                        image_path = image_filename
                        st.success(f"Image saved successfully as {uploaded_file.name}")
                    except Exception as e:
                        st.error(f"An error occurred while saving the image: {str(e)}")
                        image_path = ""
    
                new_row = {
                    'event id': event_id,
                    'location': selected_location,
                    'Element': category,
                    'Event Detector Name': Event_Detector_Name,
                    'Date': datetime.now(egypt_tz).replace(tzinfo=None),
                    'Rating': Rating,
                    'comment': comment,
                    'responsible person': responsible_person,
                    'Expected repair Date': '',
                    'Actual Repair Date': '',
                    'image path': image_path
                }
    
                new_row_df = pd.DataFrame([new_row])
                st.session_state.checklist_df = pd.concat([st.session_state.checklist_df, new_row_df], ignore_index=True)
                st.session_state.checklist_df.to_csv('checklist_records.csv', encoding='utf-8', index=False)
                st.success(f"Event recorded successfully! '{category}'!")

                    

    with col2:
        st.markdown("""
        <div style="border: 2px solid #ffeb3b; padding: 20px; background-color: #e0f7fa; color: #007BFF; border-radius: 5px; width: 100%">
            <h4 style='text-align: center;color: blue;'>Inspection Rating System.</h4>
            <ul style="color: green;">
                <li style="font-size: 18px;">0: Good condition. Well, maintained, no action required. Satisfactory Performance</li>
                <li style="font-size: 18px;">1: Moderate condition. Should monitor. Satisfactory Performance.</li>
                <li style="font-size: 18px;">2: Degraded condition. Routine maintenance and repair needed. Unsatisfactory Performance.</li>
                <li style="font-size: 18px;">3: Serious condition. Immediate need for repair or replacement. Unsatisfactory Performance.</li>
                <li style="font-size: 18px;">N/A :Not applicable</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        st.subheader('Updated Checklist Data.')
        st.dataframe(st.session_state.checklist_df)
        st.button("Update page")
        excel_data = to_excel(st.session_state.checklist_df)

# زر التنزيل لصيغة Excel
        st.download_button(
            label="Download Checklist as Excel",
            data=excel_data,
            file_name='checklist_records.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
if page == 'Work Shop Order':
    st.title('Repair status update')

    # إنشاء تخطيط أفقي بعمودين
    col1, col2 = st.columns([2, 3])

    # الجزء الأول: لاختيار رقم الحدث وإدخال اسم المعدل
    with col1:
        if not st.session_state.checklist_df.empty:
            selected_names = st.multiselect('Select Responsible Person(s)', repair_personnel)
            filtered_events = st.session_state.checklist_df[st.session_state.checklist_df['responsible person'].isin(selected_names)]

            if not filtered_events.empty:
                event_ids = filtered_events['event id'].tolist()
                selected_event_id = st.selectbox('Select Event ID', event_ids)

                if selected_event_id:
                    selected_event = filtered_events[filtered_events['event id'] == selected_event_id]
                    if not selected_event.empty:
                        st.session_state.selected_event = selected_event  # حفظ الحدث المحدد في الحالة

                modifier_name = st.text_input('Modifier Name')

                if modifier_name in repair_personnel:
                    Expected_repair_Date = st.date_input('Expected repair Date')
                    Actual_Repair_Date = st.date_input('Actual Repair Date')
                    update_start_button = st.button('Update Expected repair Date')
                    update_end_button = st.button('Update Actual Repair Date')

                    if update_start_button:
                        if selected_event_id in st.session_state.checklist_df['event id'].values:
                            st.session_state.checklist_df.loc[st.session_state.checklist_df['event id'] == selected_event_id, 'Expected repair Date'] = Expected_repair_Date.strftime('%Y-%m-%d')
                            st.session_state.checklist_df.to_csv('checklist_records.csv', encoding='utf-8', index=False)
                            st.success('Expected repair Date Updated successfully')
                            
                            new_log_entry = {
                                'event id': selected_event_id,
                                'modifier name': modifier_name,
                                'modification Date': datetime.now(egypt_tz).replace(tzinfo=None),
                                'modification type': 'update Expected repair Date',
                                'new Date': Expected_repair_Date.strftime('%Y-%m-%d')
                            }
                            new_log_df = pd.DataFrame([new_log_entry])
                            st.session_state.log_df = pd.concat([st.session_state.log_df, new_log_df], ignore_index=True)
                            st.session_state.log_df.to_csv('change_log.csv', encoding='utf-8',  index=False)

                    if update_end_button:
                        if selected_event_id in st.session_state.checklist_df['event id'].values:
                            st.session_state.checklist_df.loc[st.session_state.checklist_df['event id'] == selected_event_id, 'Actual Repair Date'] = Actual_Repair_Date.strftime('%Y-%m-%d')
                            st.session_state.checklist_df.to_csv('checklist_records.csv', index=False)
                            st.success('Actual Repair Date Updated successfully')
                            
                            new_log_entry = {
                                'event id': selected_event_id,
                                'modifier name': modifier_name,
                                'modification Date': datetime.now(egypt_tz).replace(tzinfo=None),
                                'modification type': 'update Actual Repair Date',
                                'new Date': Actual_Repair_Date.strftime('%Y-%m-%d')
                            }
                            new_log_df = pd.DataFrame([new_log_entry])
                            st.session_state.log_df = pd.concat([st.session_state.log_df, new_log_df], ignore_index=True)
                            st.session_state.log_df.to_csv('change_log.csv', index=False)
            else:
                st.warning("No events found for the selected person(s).")
        else:
            st.warning("No checklist data available.")
    st.button("Update page")
    # الجزء الثاني: عرض تفاصيل الحدث المحدد
    with col2:
        if 'selected_event' in st.session_state and not st.session_state.selected_event.empty:
            selected_event = st.session_state.selected_event
            
            # عرض تفاصيل الحدث ك DataFrame
            st.dataframe(selected_event)

            # عرض الصورة إذا كانت موجودة
            image_path = selected_event['image path'].values[0]
            if isinstance(image_path, str) and image_path and os.path.exists(image_path):
                st.image(image_path, caption=f'Image for Event {selected_event["event id"].values[0]}', width=300)
            else:
                st.warning("Image not found or path is invalid.")

        else:
            st.warning("Select an event to view details.")
    
elif page == 'View Change Log':
    st.title('View Change Log')

    change_log = load_change_log()
    st.write(change_log)
    excel_data = to_excel(st.session_state.log_df)

# زر التنزيل لصيغة Excel
    st.download_button(
        label="Download Checklist as Excel",
        data=excel_data,
        file_name='change_log.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    

elif page == 'Clear data':
    st.title('Clear Data')
    if st.button('Clear Checklist Data'):
        st.session_state.checklist_df = pd.DataFrame(columns=[
            'event id', 'location', 'Element', 'Event Detector Name', 
            'Date', 'Rating', 'responsible person', 
            'Expected repair Date', 'Actual Repair Date', 'image path', 'comment'
        ])
        st.session_state.checklist_df.to_excel('checklist_records.xlsx', index=False)
        st.success('Checklist data cleared!')

    if st.button('Clear Log Data'):
        st.session_state.log_df = pd.DataFrame(columns=[
            'event id', 'modifier name', 'modification Date', 
            'modification type', 'new Date'
        ])
        st.session_state.log_df.to_excel('change_log.xlsx', index=False)
        st.success('Log data cleared!')
