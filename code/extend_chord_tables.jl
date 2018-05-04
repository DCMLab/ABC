include("regex.jl")
include("movement_iterator.jl")

using DataFrames

function get_feature(chord, feature, default="", regex=regex)
    m = match(regex, chord)
    if m != nothing && m[feature] != nothing
        m[feature]
    else
        default
    end
end

function extend_chord_table(df)
    # add global_key column
    df[:global_key] = match(regex, df[1, :chords])[:key]

    # add local_key column
    df[:local_key] = ""
    df[1, :local_key] = "I"

    for i in 2:size(df, 1)
        df[i, :local_key] = get_feature(df[i, :chords], :key, df[i-1, :local_key])
    end

    # add organ column
    df[:organ] = ""
    df[1, :organ] = get_feature(df[1, :chords], :organ)

    for i in 2:size(df, 1)
        m = match(regex, df[i, :chords])
        df[i, :organ] = if m != nothing && m[:organ] != nothing
            m[:organ]
        elseif match(regex, df[i-1, :chords]) != nothing && match(regex, df[i-1, :chords])[:organend] != nothing
            ""
        else
            df[i-1, :organ]
        end
    end

    # add columns for numeral, form, figbass, changes, relativeroot
    for f in (:numeral, :form, :figbass, :changes, :relativeroot)
        df[f] = map(c->get_feature(c, f), df[:chords])
    end

    # add column for phraseend
    df[:phraseend] = map(df[:chords]) do chord
        m = match(regex, chord)
        m != nothing && m[:phraseend] != nothing
    end

    df
end

for file in movements()
    writetable(file, extend_chord_table(readtable(file)))
end
