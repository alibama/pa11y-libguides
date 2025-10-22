import streamlit as st
import pandas as pd
import re
from collections import Counter
import plotly.express as px
import plotly.graph_objects as go

def normalize_error_message(error):
    """Normalize error messages to group similar issues"""
    error = error.strip()
    
    # Common patterns to normalize
    patterns = [
        # Button naming issues
        (r'This button element does not have a name available.*', 'Button missing accessible name'),
        
        # Input/form labeling issues
        (r'This textinput element does not have a name available.*', 'Text input missing accessible name'),
        (r'This form field should be labelled in some way.*', 'Form field missing label'),
        
        # Contrast issues - normalize to generic contrast issue
        (r'This element has insufficient contrast.*Expected.*ratio of at least [\d.]+:1.*', 'Insufficient color contrast'),
        
        # Duplicate ID issues
        (r'Duplicate id attribute value.*found on the web page.*', 'Duplicate ID attribute'),
        
        # Iframe issues
        (r'Iframe element requires a non-empty title attribute.*', 'Iframe missing title attribute'),
        
        # Obsolete markup
        (r'Presentational markup used that has become obsolete in HTML5.*', 'Obsolete HTML5 markup'),
        
        # Image alt text issues
        (r'Img element.*missing alt text.*', 'Image missing alt text'),
        
        # Link issues
        (r'.*link.*missing.*text.*', 'Link missing descriptive text'),
    ]
    
    for pattern, normalized in patterns:
        if re.search(pattern, error, re.IGNORECASE):
            return normalized
    
    # If no pattern matches, return first 80 characters
    return error[:80] + ('...' if len(error) > 80 else '')

def extract_errors_from_row(errors_text):
    """Extract individual errors from the pipe-separated string"""
    if pd.isna(errors_text) or errors_text == '':
        return []
    
    # Split by pipe and clean up
    errors = [error.strip() for error in str(errors_text).split('|') if error.strip()]
    return errors

def analyze_wcag_categories(error):
    """Categorize errors by WCAG principles"""
    error_lower = error.lower()
    
    if any(word in error_lower for word in ['contrast', 'color']):
        return 'Perceivable (Colors/Contrast)'
    elif any(word in error_lower for word in ['button', 'input', 'form', 'label', 'name', 'title']):
        return 'Operable (Navigation/Forms)'
    elif any(word in error_lower for word in ['markup', 'html5', 'obsolete']):
        return 'Robust (Code Quality)'
    elif any(word in error_lower for word in ['alt', 'image', 'img']):
        return 'Perceivable (Images/Media)'
    else:
        return 'Other'

def main():
    st.set_page_config(
        page_title="PA11Y Issue Aggregator",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 PA11Y Accessibility Issue Aggregator")
    st.write("Upload your PA11Y results CSV to analyze and prioritize common accessibility issues")
    
    # File upload
    uploaded_file = st.file_uploader("Choose your PA11Y results CSV file", type="csv")
    
    if uploaded_file is not None:
        try:
            # Read the CSV
            df = pd.read_csv(uploaded_file)
            
            # Validate required columns
            if 'all_errors' not in df.columns:
                st.error("CSV must contain an 'all_errors' column. Please upload a file from the PA11Y analyzer.")
                st.stop()
            
            st.success(f"✅ Loaded {len(df)} URLs for analysis")
            
            # Extract all individual errors
            all_errors = []
            url_error_map = {}  # Track which URLs have which errors
            
            for idx, row in df.iterrows():
                url = row.get('URL', f'Row {idx}')
                errors = extract_errors_from_row(row['all_errors'])
                
                for error in errors:
                    normalized_error = normalize_error_message(error)
                    all_errors.append({
                        'original_error': error,
                        'normalized_error': normalized_error,
                        'url': url,
                        'wcag_category': analyze_wcag_categories(error)
                    })
                    
                    # Track URL-error mapping
                    if normalized_error not in url_error_map:
                        url_error_map[normalized_error] = set()
                    url_error_map[normalized_error].add(url)
            
            if not all_errors:
                st.warning("No accessibility errors found in the uploaded file.")
                st.stop()
            
            # Create DataFrame for analysis
            errors_df = pd.DataFrame(all_errors)
            
            # Summary statistics
            st.write("## 📈 Summary Statistics")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Errors", len(all_errors))
            with col2:
                st.metric("Unique Error Types", len(set(errors_df['normalized_error'])))
            with col3:
                urls_with_errors = len(df[df['pa11y_errors'] != '0'])
                st.metric("URLs with Errors", urls_with_errors)
            with col4:
                avg_errors = round(len(all_errors) / len(df), 1)
                st.metric("Avg Errors per URL", avg_errors)
            
            # Top issues analysis
            st.write("## 🎯 Priority Issues (Most Common)")
            
            # Count occurrences of each normalized error
            error_counts = errors_df['normalized_error'].value_counts()
            
            # Add URL count for each error type
            priority_data = []
            for error_type, count in error_counts.items():
                url_count = len(url_error_map[error_type])
                priority_data.append({
                    'Issue Type': error_type,
                    'Total Occurrences': count,
                    'URLs Affected': url_count,
                    'Impact Score': count * url_count  # Simple impact calculation
                })
            
            priority_df = pd.DataFrame(priority_data)
            
            # Display top 10 issues
            st.dataframe(
                priority_df.head(10),
                use_container_width=True,
                hide_index=True
            )
            
            # Visualizations
            st.write("## 📊 Issue Analysis")
            
            # Top 15 issues bar chart
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("### Most Frequent Issues")
                top_15_issues = priority_df.head(15)
                fig1 = px.bar(
                    top_15_issues, 
                    x='Total Occurrences', 
                    y='Issue Type',
                    title="Top 15 Most Common Issues",
                    orientation='h'
                )
                fig1.update_layout(height=500, yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig1, use_container_width=True)
            
            with col2:
                st.write("### Issues by WCAG Category")
                wcag_counts = errors_df['wcag_category'].value_counts()
                fig2 = px.pie(
                    values=wcag_counts.values,
                    names=wcag_counts.index,
                    title="Distribution by WCAG Category"
                )
                st.plotly_chart(fig2, use_container_width=True)
            
            # Impact vs frequency scatter
            st.write("### Impact vs Frequency Analysis")
            fig3 = px.scatter(
                priority_df,
                x='URLs Affected',
                y='Total Occurrences',
                size='Impact Score',
                hover_data=['Issue Type'],
                title="Issue Impact Analysis (Size = Impact Score)",
                labels={
                    'URLs Affected': 'Number of URLs Affected',
                    'Total Occurrences': 'Total Number of Occurrences'
                }
            )
            st.plotly_chart(fig3, use_container_width=True)
            
            # Detailed breakdown
            st.write("## 🔍 Detailed Issue Breakdown")
            
            # Allow user to select an issue type for detailed view
            selected_issue = st.selectbox(
                "Select an issue type to see affected URLs:",
                options=priority_df['Issue Type'].tolist()
            )
            
            if selected_issue:
                # Show URLs affected by this issue
                affected_urls = list(url_error_map[selected_issue])
                
                st.write(f"### URLs affected by: {selected_issue}")
                st.write(f"**{len(affected_urls)} URLs affected:**")
                
                # Create a DataFrame for affected URLs
                affected_df = pd.DataFrame({'Affected URLs': affected_urls})
                st.dataframe(affected_df, use_container_width=True, hide_index=True)
                
                # Show sample of original error messages for context
                sample_errors = errors_df[errors_df['normalized_error'] == selected_issue]['original_error'].unique()[:3]
                
                with st.expander("Sample original error messages"):
                    for i, error in enumerate(sample_errors, 1):
                        st.write(f"{i}. {error}")
            
            # Export options
            st.write("## 📥 Export Results")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Download priority issues
                priority_csv = priority_df.to_csv(index=False)
                st.download_button(
                    label="📊 Download Priority Issues CSV",
                    data=priority_csv,
                    file_name="accessibility_priority_issues.csv",
                    mime="text/csv"
                )
            
            with col2:
                # Download detailed breakdown
                detailed_csv = errors_df.to_csv(index=False)
                st.download_button(
                    label="📋 Download Detailed Breakdown CSV",
                    data=detailed_csv,
                    file_name="accessibility_detailed_breakdown.csv",
                    mime="text/csv"
                )
            
            # Recommendations
            st.write("## 💡 Recommendations")
            
            top_3_issues = priority_df.head(3)
            
            recommendations = {
                'Button missing accessible name': '1. Add aria-label, aria-labelledby, or visible text to buttons\n2. Use descriptive button text instead of just icons',
                'Text input missing accessible name': '1. Associate inputs with <label> elements\n2. Use aria-label or aria-labelledby attributes\n3. Ensure form labels are descriptive',
                'Insufficient color contrast': '1. Use darker colors for text\n2. Test with color contrast analyzers\n3. Ensure 4.5:1 ratio for normal text, 3:1 for large text',
                'Form field missing label': '1. Use <label for="input-id"> elements\n2. Add aria-label attributes\n3. Group related fields with fieldset/legend',
                'Duplicate ID attribute': '1. Ensure all IDs are unique on the page\n2. Use classes instead of IDs for styling\n3. Validate HTML for duplicate IDs'
            }
            
            for _, issue in top_3_issues.iterrows():
                issue_type = issue['Issue Type']
                st.write(f"### {issue_type}")
                st.write(f"**Affects {issue['URLs Affected']} URLs with {issue['Total Occurrences']} occurrences**")
                
                if issue_type in recommendations:
                    st.write("**Recommended fixes:**")
                    st.write(recommendations[issue_type])
                else:
                    st.write("Review the original error messages for specific guidance.")
                st.write("---")
                
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            st.write("Please ensure your CSV file has the correct format with 'URL', 'pa11y_errors', and 'all_errors' columns.")

if __name__ == "__main__":
    main()
