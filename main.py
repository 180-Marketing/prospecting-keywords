import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from openai import OpenAI
import re

# Set page configuration
st.set_page_config(
    page_title="Link Building Prospecting Keywords Tool",
    page_icon="🔗",
    layout="wide"
)

# Set page title
st.title("Link Building Prospecting Keywords Tool")
st.markdown("Generate targeted prospecting keywords for link building based on a website's meta description.")

# Create two columns for input
col1, col2 = st.columns(2)

# Input for URL and API key
with col1:
    url = st.text_input("Enter a URL to analyze:", placeholder="https://example.com")
    
with col2:
    api_key = st.text_input("Enter your OpenAI API key:", type="password", placeholder="sk-...")

# Process when both inputs are provided
if url and api_key:
    # Create a container for results with a spinner
    with st.spinner("Processing URL and generating keywords..."):
        try:
            # Extract root domain
            parsed_url = urlparse(url)
            root_domain = parsed_url.netloc
            if root_domain.startswith('www.'):
                root_domain = root_domain[4:]
            
            st.write(f"Root Domain: **{root_domain}**")
            
            # Scrape meta description
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            meta_description = ""
            
            # Try different meta tags to find description
            meta_tags = [
                soup.find('meta', attrs={'name': 'description'}),
                soup.find('meta', attrs={'property': 'og:description'}),
                soup.find('meta', attrs={'name': 'twitter:description'})
            ]
            
            for meta_tag in meta_tags:
                if meta_tag and meta_tag.get('content'):
                    meta_description = meta_tag.get('content')
                    break
            
            if meta_description:
                st.write("**Meta Description:**")
                st.info(meta_description)
            else:
                st.warning("No meta description found for this URL. Using domain name only.")
                meta_description = f"Website with domain {root_domain}"
            
            # Create prompt for GPT-4o
            prompt = f"""# Task Instructions 
You are a Link Builder for {root_domain}. Your task is to create a list of 5 prospecting keywords that, when searched in Google, will help you find blogs and websites that are relevant to {root_domain}'s products. These blogs should be potential candidates for link building opportunities.
First, review the website's meta description to better understand the website's products and industry.
<meta_description>
{meta_description}
</meta_description>
Next, follow these instructions step-by-step. 
Step 1. Identify the 3 most relevant keywords that describe the website's main top-level categories.
Step 2. Identify the 3 most relevant keywords that describe the website's specific product categories.
Step 3. Identify the 3 most relevant keywords that describe the website's broader categories.
Step 4. Identify the 3 most relevant industry the website belongs to.
Step 5. Review the final list of all keywords and select just the top 5 most relevant keywords that would match relevant article titles.
Guidelines
 - All keywords must be short and only contain 1-2 words so they can match more relevant articles.
 - Skip any overly general keywords that could return irrelevant blogs and websites for a different search intent.
 - Avoid the use of adjectives (cheap, used, etc.). 
 - Avoid overly generic terms or common words that have multiple meanings/applications and could match irrelevant articles (equipment, tools, DIY, solutions).
# Output Format 
Provide a separate list for each of the steps above. Present your list of keywords in the following format:
<step_1_keywords>
1. [Keyword 1]
2. [Keyword 2]
3. [Keyword 3]
...
</step_1_keywords>
<step_2_keywords>
1. [Keyword 1]
2. [Keyword 2]
3. [Keyword 3]
...
</step_2_keywords>
Remember to focus on keywords that will help you find relevant articles that are likely to be interested in the client's products and could potentially become link building partners.
"""
            
            # Make OpenAI API call
            try:
                # For newer versions of OpenAI Python library
                client = OpenAI(api_key=api_key)
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are a helpful link building assistant."},
                        {"role": "user", "content": prompt}
                    ]
                )
            except TypeError:
                # For older versions of OpenAI Python library
                import openai
                openai.api_key = api_key
                response = openai.ChatCompletion.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are a helpful link building assistant."},
                        {"role": "user", "content": prompt}
                    ]
                )
                response.choices[0].message = type('obj', (object,), {
                    'content': response.choices[0].message.content
                })
            
            # Extract response
            gpt_response = response.choices[0].message.content
            
            # Extract keywords using multiple fallback methods
            keywords = []
            
            # Method 1: Try to extract from step_5_keywords tags
            step_5_pattern = r'<step_5_keywords>(.*?)</step_5_keywords>'
            final_keywords_match = re.search(step_5_pattern, gpt_response, re.DOTALL)
            
            if final_keywords_match:
                final_keywords_text = final_keywords_match.group(1).strip()
                lines = final_keywords_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and re.match(r'^\d+\.', line):
                        # Extract keyword - try with brackets format first
                        keyword_match = re.search(r'\[(.*?)\]', line)
                        if keyword_match:
                            keywords.append(keyword_match.group(1).strip())
                        else:
                            # If no brackets, just take what's after the number and period
                            keyword = re.sub(r'^\d+\.\s*', '', line).strip()
                            keywords.append(keyword)
            
            # Method 2: Look for "Step 5" or "Top 5" heading if no keywords found yet
            if not keywords:
                # Various patterns to match step 5 section
                step5_patterns = [
                    r'Step 5[\s\-\:\.]+([^#]+)',
                    r'top 5 most relevant keywords[\s\-\:\.]+([^#]+)', 
                    r'final list of.*?keywords[\s\-\:\.]+([^#]+)'
                ]
                
                for pattern in step5_patterns:
                    match = re.search(pattern, gpt_response, re.IGNORECASE | re.DOTALL)
                    if match:
                        section_text = match.group(1).strip()
                        lines = section_text.split('\n')
                        for line in lines:
                            line = line.strip()
                            if line and re.match(r'^\d+[\.\)]', line):
                                # Try extracting with various formats
                                keyword_match = re.search(r'\[(.*?)\]', line)
                                if keyword_match:
                                    keywords.append(keyword_match.group(1).strip())
                                else:
                                    # Extract what's after the number and period/parenthesis
                                    keyword = re.sub(r'^\d+[\.\)]\s*', '', line).strip()
                                    # Remove other formatting like quotes or extra brackets
                                    keyword = re.sub(r'^["\'`\[]|["\'`\]]
                
                # Display results
                st.subheader("Top 5 Prospecting Keywords:")
                
                if keywords:
                    # Create columns for keyword display
                    keyword_cols = st.columns(5)
                    for i, kw in enumerate(keywords):
                        with keyword_cols[i]:
                            st.metric(f"Keyword {i+1}", kw)
                    
                    # Show comma-separated list
                    st.success(", ".join(keywords))
                    
                    # Create a download button for the keywords
                    st.download_button(
                        label="Download Keywords as CSV",
                        data=",".join(keywords),
                        file_name=f"{root_domain}_keywords.csv",
                        mime="text/csv"
                    )
                else:
                    st.error("Could not parse keywords from the response.")
                
                # Show full analysis
                with st.expander("View complete keyword analysis"):
                    st.write(gpt_response)
            else:
                st.warning("Keyword extraction had limited results. Please check the complete response.")
                st.text_area("GPT-4o Response for Manual Review:", value=gpt_response, height=300)
                
                # Add instructions for manual extraction
                st.info("""
                It appears the AI didn't format the response as expected. To manually extract keywords:
                1. Look for sections labeled "Step 5" or "Final keywords"
                2. Identify numbered lists with short 1-2 word phrases
                3. Select the 5 most relevant keywords from the response
                """)
                
                # Add a form for manual keyword entry
                with st.form("manual_keywords"):
                    st.subheader("Enter Keywords Manually")
                    manual_keywords = st.text_input("Enter up to 5 keywords separated by commas:")
                    submit_button = st.form_submit_button("Save Keywords")
                    
                    if submit_button and manual_keywords:
                        keywords = [k.strip() for k in manual_keywords.split(",")][:5]
                        st.success(f"Manually added keywords: {', '.join(keywords)}")
                        
                        # Create a download button for the keywords
                        st.download_button(
                            label="Download Keywords as CSV",
                            data=",".join(keywords),
                            file_name=f"{root_domain}_keywords.csv",
                            mime="text/csv"
                        )
                
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            if "Invalid API key" in str(e):
                st.warning("Please check your OpenAI API key. Make sure it has access to the GPT-4o model.")

# Add instructions and information
st.markdown("""
---
### How to use this tool:
1. Enter a URL you want to analyze
2. Provide your OpenAI API key (it's only used for this request and not stored)
3. The tool will extract the root domain and meta description from the URL
4. It will generate prospecting keywords using GPT-4o
5. The results will show the top 5 keywords for link building opportunities

### Requirements:
- OpenAI API key with access to the GPT-4o model
- Valid URL with meta description (or at least accessible website)
""")

# Add footer
st.markdown("---")
st.markdown("🔗 Link Building Prospecting Keywords Tool | Built with Streamlit + OpenAI")
, '', keyword).strip()
                                    if keyword:
                                        keywords.append(keyword)
                        break  # Stop after finding the first matching pattern
            
            # Method 3: Last resort - look for any numbered list with short entries
            if not keywords:
                # Find all numbered lists in the response
                list_pattern = r'^\d+[\.\)]\s*(.*?)
                
                # Display results
                st.subheader("Top 5 Prospecting Keywords:")
                
                if keywords:
                    # Create columns for keyword display
                    keyword_cols = st.columns(5)
                    for i, kw in enumerate(keywords):
                        with keyword_cols[i]:
                            st.metric(f"Keyword {i+1}", kw)
                    
                    # Show comma-separated list
                    st.success(", ".join(keywords))
                    
                    # Create a download button for the keywords
                    st.download_button(
                        label="Download Keywords as CSV",
                        data=",".join(keywords),
                        file_name=f"{root_domain}_keywords.csv",
                        mime="text/csv"
                    )
                else:
                    st.error("Could not parse keywords from the response.")
                
                # Show full analysis
                with st.expander("View complete keyword analysis"):
                    st.write(gpt_response)
            else:
                st.error("Could not find the final keywords section in the GPT response.")
                with st.expander("View GPT response"):
                    st.write(gpt_response)
                
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            if "Invalid API key" in str(e):
                st.warning("Please check your OpenAI API key. Make sure it has access to the GPT-4o model.")

# Add instructions and information
st.markdown("""
---
### How to use this tool:
1. Enter a URL you want to analyze
2. Provide your OpenAI API key (it's only used for this request and not stored)
3. The tool will extract the root domain and meta description from the URL
4. It will generate prospecting keywords using GPT-4o
5. The results will show the top 5 keywords for link building opportunities

### Requirements:
- OpenAI API key with access to the GPT-4o model
- Valid URL with meta description (or at least accessible website)
""")

# Add footer
st.markdown("---")
st.markdown("🔗 Link Building Prospecting Keywords Tool | Built with Streamlit + OpenAI")

                all_items = re.findall(list_pattern, gpt_response, re.MULTILINE)
                
                # Filter to short entries that are likely keywords (1-3 words)
                potential_keywords = [item.strip() for item in all_items if len(item.split()) <= 3]
                
                # Clean up formatting
                for item in potential_keywords:
                    clean_item = re.sub(r'^["\'`\[]|["\'`\]]
                
                # Display results
                st.subheader("Top 5 Prospecting Keywords:")
                
                if keywords:
                    # Create columns for keyword display
                    keyword_cols = st.columns(5)
                    for i, kw in enumerate(keywords):
                        with keyword_cols[i]:
                            st.metric(f"Keyword {i+1}", kw)
                    
                    # Show comma-separated list
                    st.success(", ".join(keywords))
                    
                    # Create a download button for the keywords
                    st.download_button(
                        label="Download Keywords as CSV",
                        data=",".join(keywords),
                        file_name=f"{root_domain}_keywords.csv",
                        mime="text/csv"
                    )
                else:
                    st.error("Could not parse keywords from the response.")
                
                # Show full analysis
                with st.expander("View complete keyword analysis"):
                    st.write(gpt_response)
            else:
                st.error("Could not find the final keywords section in the GPT response.")
                with st.expander("View GPT response"):
                    st.write(gpt_response)
                
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            if "Invalid API key" in str(e):
                st.warning("Please check your OpenAI API key. Make sure it has access to the GPT-4o model.")

# Add instructions and information
st.markdown("""
---
### How to use this tool:
1. Enter a URL you want to analyze
2. Provide your OpenAI API key (it's only used for this request and not stored)
3. The tool will extract the root domain and meta description from the URL
4. It will generate prospecting keywords using GPT-4o
5. The results will show the top 5 keywords for link building opportunities

### Requirements:
- OpenAI API key with access to the GPT-4o model
- Valid URL with meta description (or at least accessible website)
""")

# Add footer
st.markdown("---")
st.markdown("🔗 Link Building Prospecting Keywords Tool | Built with Streamlit + OpenAI")
, '', item).strip()
                    if clean_item and clean_item not in keywords:
                        keywords.append(clean_item)
            
            # Method 4: If still nothing, try to find any short phrases that look like keywords
            if not keywords:
                # Look for phrases in quotes or brackets that are 1-3 words
                quote_patterns = [r'"([^"]{1,30})"', r"'([^']{1,30})'", r"\[([^\]]{1,30})\]"]
                for pattern in quote_patterns:
                    potential_words = re.findall(pattern, gpt_response)
                    for word in potential_words:
                        if len(word.split()) <= 3 and word.strip() not in keywords:
                            keywords.append(word.strip())
            
            # Ensure we have only 5 keywords
            keywords = keywords[:5]
            
            # If still no keywords, add debugging message
            if not keywords:
                st.warning("Could not automatically extract keywords. Please check the GPT-4o response below and manually identify keywords.")
                # Display the GPT-4o response for the user to see
                st.text_area("GPT-4o Response:", value=gpt_response, height=400)
                
                # Display results
                st.subheader("Top 5 Prospecting Keywords:")
                
                if keywords:
                    # Create columns for keyword display
                    keyword_cols = st.columns(5)
                    for i, kw in enumerate(keywords):
                        with keyword_cols[i]:
                            st.metric(f"Keyword {i+1}", kw)
                    
                    # Show comma-separated list
                    st.success(", ".join(keywords))
                    
                    # Create a download button for the keywords
                    st.download_button(
                        label="Download Keywords as CSV",
                        data=",".join(keywords),
                        file_name=f"{root_domain}_keywords.csv",
                        mime="text/csv"
                    )
                else:
                    st.error("Could not parse keywords from the response.")
                
                # Show full analysis
                with st.expander("View complete keyword analysis"):
                    st.write(gpt_response)
            else:
                st.error("Could not find the final keywords section in the GPT response.")
                with st.expander("View GPT response"):
                    st.write(gpt_response)
                
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            if "Invalid API key" in str(e):
                st.warning("Please check your OpenAI API key. Make sure it has access to the GPT-4o model.")

# Add instructions and information
st.markdown("""
---
### How to use this tool:
1. Enter a URL you want to analyze
2. Provide your OpenAI API key (it's only used for this request and not stored)
3. The tool will extract the root domain and meta description from the URL
4. It will generate prospecting keywords using GPT-4o
5. The results will show the top 5 keywords for link building opportunities

### Requirements:
- OpenAI API key with access to the GPT-4o model
- Valid URL with meta description (or at least accessible website)
""")

# Add footer
st.markdown("---")
st.markdown("🔗 Link Building Prospecting Keywords Tool | Built with Streamlit + OpenAI")
