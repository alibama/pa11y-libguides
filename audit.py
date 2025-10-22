import streamlit as st
import pandas as pd
import subprocess
import tempfile
import os
import re
import time
from io import StringIO

def check_pa11y_installed():
    """Check if pa11y is installed"""
    try:
        subprocess.run(['pa11y', '--version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def run_pa11y_on_url(url):
    """Run pa11y on a single URL and return results"""
    try:
        # Run pa11y with explicit options
        result = subprocess.run(
            ['pa11y', '--reporter', 'cli', '--threshold', '0', url],
            capture_output=True,
            text=True,
            timeout=30  # 30 second timeout per URL
        )
        
        if result.returncode != 0 and not result.stdout:
            return {
                'error_count': 'FAILED',
                'errors': 'URL unreachable or pa11y error',
                'raw_output': result.stderr
            }
        
        # Parse the output
        output_lines = result.stdout.split('\n')
        
        # Count errors
        error_lines = [line for line in output_lines if line.strip().startswith('• Error:')]
        error_count = len(error_lines)
        
        # Extract error messages
        errors = []
        for line in error_lines:
            # Remove the bullet and "Error:" prefix
            clean_error = re.sub(r'^• Error:\s*', '', line.strip())
            if clean_error:
                errors.append(clean_error)
        
        return {
            'error_count': error_count,
            'errors': ' | '.join(errors) if errors else '',
            'raw_output': result.stdout
        }
        
    except subprocess.TimeoutExpired:
        return {
            'error_count': 'TIMEOUT',
            'errors': 'Request timed out after 30 seconds',
            'raw_output': ''
        }
    except Exception as e:
        return {
            'error_count': 'ERROR',
            'errors': f'Exception: {str(e)}',
            'raw_output': ''
        }

def main():
    st.set_page_config(
        page_title="PA11Y Accessibility Checker",
        page_icon="♿",
        layout="wide"
    )
    
    st.title("♿ PA11Y Accessibility Checker")
    st.write("Upload a CSV file with URLs and get real-time accessibility analysis")
    
    # Check if pa11y is installed
    if not check_pa11y_installed():
        st.error("❌ PA11Y is not installed!")
        st.write("Install it with: `npm install -g pa11y`")
        st.stop()
    else:
        st.success("✅ PA11Y is installed and ready")
    
    # File upload
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    if uploaded_file is not None:
        # Read the CSV
        try:
            df = pd.read_csv(uploaded_file)
            st.write("### Original Data Preview")
            st.dataframe(df.head())
            
            # Let user select URL column
            url_columns = df.columns.tolist()
            url_column = st.selectbox("Select the column containing URLs:", url_columns)
            
            if st.button("Start PA11Y Analysis", type="primary"):
                # Initialize results columns
                df['pa11y_errors'] = ''
                df['all_errors'] = ''
                
                # Create placeholders for real-time updates
                progress_bar = st.progress(0)
                status_text = st.empty()
                results_placeholder = st.empty()
                
                total_urls = len(df)
                
                # Process each URL
                for idx, row in df.iterrows():
                    url = str(row[url_column]).strip()
                    
                    if pd.isna(url) or url == '' or url == 'nan':
                        df.loc[idx, 'pa11y_errors'] = 'NO_URL'
                        df.loc[idx, 'all_errors'] = 'No URL provided'
                        continue
                    
                    # Update status
                    status_text.text(f"Processing URL {idx + 1} of {total_urls}: {url}")
                    
                    # Run pa11y
                    result = run_pa11y_on_url(url)
                    
                    # Update dataframe
                    df.loc[idx, 'pa11y_errors'] = result['error_count']
                    df.loc[idx, 'all_errors'] = result['errors']
                    
                    # Update progress
                    progress_bar.progress((idx + 1) / total_urls)
                    
                    # Show current results
                    results_placeholder.dataframe(df)
                    
                    # Small delay to make updates visible
                    time.sleep(0.1)
                
                status_text.text("✅ Analysis complete!")
                
                # Final results
                st.write("### Final Results")
                st.dataframe(df)
                
                # Summary statistics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    total_errors = df[df['pa11y_errors'].apply(lambda x: str(x).isdigit())]['pa11y_errors'].astype(int).sum()
                    st.metric("Total Errors Found", total_errors)
                
                with col2:
                    urls_with_errors = len(df[(df['pa11y_errors'].apply(lambda x: str(x).isdigit())) & (df['pa11y_errors'].astype(int) > 0)])
                    st.metric("URLs with Errors", urls_with_errors)
                
                with col3:
                    failed_urls = len(df[df['pa11y_errors'].isin(['FAILED', 'TIMEOUT', 'ERROR'])])
                    st.metric("Failed URLs", failed_urls)
                
                # Download button for results
                csv_buffer = StringIO()
                df.to_csv(csv_buffer, index=False)
                csv_string = csv_buffer.getvalue()
                
                st.download_button(
                    label="📥 Download Results as CSV",
                    data=csv_string,
                    file_name=f"pa11y_results_{int(time.time())}.csv",
                    mime="text/csv"
                )
                
                # Show detailed view for URLs with errors
                error_df = df[(df['pa11y_errors'].apply(lambda x: str(x).isdigit())) & (df['pa11y_errors'].astype(int) > 0)]
                if not error_df.empty:
                    st.write("### URLs with Accessibility Errors")
                    st.dataframe(error_df[[url_column, 'pa11y_errors', 'all_errors']])
                
        except Exception as e:
            st.error(f"Error reading CSV file: {str(e)}")
            st.write("Please make sure your CSV file is properly formatted.")

if __name__ == "__main__":
    main()
