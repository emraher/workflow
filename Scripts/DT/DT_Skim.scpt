tell application ":Applications:DEVONthink Pro.app"
	set pdfFile to the content record of the think window 1
	set RecordLink to the reference URL of pdfFile
	set PdfPage to current page of the think window 1
	set DevonThinkLink to RecordLink & "?page=" & PdfPage
	set the clipboard to DevonThinkLink
	set PdfPath to get the path of pdfFile
	set PdfPath to (POSIX file PdfPath) as Unicode text
	close the think window 1
 
	tell application "Skim"
	    activate
		open file PdfPath
		set PdfPage to PdfPage + 1
		go document 1 to page PdfPage of document 1
	end tell
end tell
