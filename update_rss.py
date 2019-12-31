import subprocess

def update(date):
    """ VERY MANUALLY update the rss """
    f = open("json/rss.xml")
    lines = f.readlines()
    f.close()

    # Insert new lines
    lines.insert(12, "    <item>\n")
    lines.insert(13, "        <title>Top LBRY channels updated</title>\n")
    lines.insert(14, "        <link>https://lbry.social/lbrynomics/top-lbry-channels</link>\n")
    lines.insert(15,
"""
            <description>
                Top LBRY channels has been updated!
                Date: {date}
            </description>
""".format(date=date))
    lines.insert(16, "    </item>\n")

    # Write output
    f = open("rss_updated.xml", "w")
    for line in lines:
        f.write(line)
    f.close()

    subprocess.run(["mv", "rss_updated.xml", "json/rss.xml"])

