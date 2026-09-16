# Section 5c: Word Clouds by Era (TF-IDF Based)

print("=" * 80)
print("WORD CLOUDS BY ERA (TF-IDF BASED)")
print("=" * 80)

# Define periods
periods = [
    ('before_2000', 1990, 1999, 'Before 2000'),
    ('2000_2015', 2000, 2015, '2000 - 2015'),
    ('after_2015', 2016, 2025, 'After 2015')
]

# Create figure with 3 subplots (1 row, 3 columns)
fig, axes = plt.subplots(1, 3, figsize=(20, 6), facecolor='#1a1a1a')

word_clouds_data = {}

for idx, (period_id, year_start, year_end, period_name) in enumerate(periods):
    print(f"\n--- {period_name.upper()} ({year_start}-{year_end}) ---")
    
    # Filter data by period
    df_period = df[(df['year'].notna()) & (df['year'] >= year_start) & (df['year'] <= year_end)]
    
    if len(df_period) > 0:
        # Create TF-IDF vectorizer for this period
        period_documents = df_period[text_col].fillna('').astype(str).tolist()
        
        period_tfidf = TfidfVectorizer(
            max_features=200,
            min_df=1,
            max_df=1.0,
            ngram_range=(1, 1),
            stop_words=list(french_stopwords),
            lowercase=True,
            strip_accents='unicode'
        )
        
        period_tfidf_matrix = period_tfidf.fit_transform(period_documents)
        period_feature_names = np.array(period_tfidf.get_feature_names_out())
        
        # Calculate mean TF-IDF scores for this period
        period_mean_tfidf = np.asarray(period_tfidf_matrix.mean(axis=0)).ravel()
        
        # Create dictionary of word -> TF-IDF score
        tfidf_scores_period = dict(zip(period_feature_names, period_mean_tfidf))
        
        # Get top 100 words by TF-IDF score
        top_100_by_tfidf = sorted(tfidf_scores_period.items(), key=lambda x: x[1], reverse=True)[:100]
        top_100_dict = dict(top_100_by_tfidf)
        
        print(f"Documents: {len(df_period):,}")
        print(f"Unique words: {len(period_feature_names):,}")
        print(f"Top 10 words (TF-IDF): {', '.join([w for w, _ in top_100_by_tfidf[:10]])}")
        
        # Generate word cloud using TF-IDF scores
        wordcloud = WordCloud(
            width=600,
            height=600,
            background_color='black',
            colormap='YlOrRd',
            max_words=100,
            relative_scaling=0.3,
            min_font_size=8,
            prefer_horizontal=0.7
        ).generate_from_frequencies(top_100_dict)
        
        # Display on subplot
        ax = axes[idx]
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        ax.set_title(f'{period_name}\n({len(df_period):,} docs, TF-IDF weighted)',
                    fontsize=12, fontweight='bold', color='#FFD700', pad=15)
        
        # Store data for export
        word_clouds_data[period_id] = {
            'period': period_name,
            'doc_count': len(df_period),
            'unique_words': len(period_feature_names),
            'top_words': top_100_by_tfidf[:50]
        }
    else:
        ax = axes[idx]
        ax.text(0.5, 0.5, f'No data for {period_name}', ha='center', va='center',
               color='#FFD700', fontsize=14, transform=ax.transAxes)
        ax.axis('off')

plt.tight_layout()
plt.savefig(images_dir / f'{notebook_prefix}_02b_word_clouds_by_era_tfidf.png', dpi=300, bbox_inches='tight', facecolor='#1a1a1a')
print("\n✓ Figure saved: images/02b_word_clouds_by_era_tfidf.png")
plt.show()

# Export statistics for each era
print("\n" + "=" * 80)
print("EXPORT SUMMARY BY ERA (TF-IDF BASED)")
print("=" * 80)

for period_id, data in word_clouds_data.items():
    period_df = pd.DataFrame(
        [(word, score) for word, score in data['top_words']],
        columns=['word', 'tfidf_score']
    )
    filename = f"tfidf_top_words_{period_id}.csv"
    period_df.to_csv(export_dir / filename, index=False)
    print(f"✓ Exported {filename}: {len(data['top_words'])} top words from {data['period']}")
