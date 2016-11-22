import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import org.json.JSONObject;
import org.openqa.selenium.JavascriptExecutor;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;

public class PLT {

	public static void main(String[] args) throws Exception {
		
		for (String arg : args) {
			System.out.println(arg);
		}
		
		String mode = args[0];
		String driver = args[1];
		System.setProperty("webdriver.chrome.driver", driver);
		
		if ("record".equals(mode)) {
			calculatePLT(args[2], 1);
			return;
		}
		
		String alexa = args[2];
		int tries = Integer.parseInt(args[3]);
		String result = args[4];
		
		BufferedReader br = new BufferedReader(new FileReader(new File(alexa)));
		String line = null;
		JSONObject mapper = new JSONObject();
		while ((line = br.readLine()) != null) {
			String website = "http://www." + line;
			JSONObject stats = calculatePLT(website, tries);
			mapper.put(line, stats);
		}
		try (BufferedWriter bw = new BufferedWriter(new FileWriter(new File(result)))) {
			bw.write(mapper.toString());
		} catch (Exception e) {
			e.printStackTrace();
		}
		System.out.println(mapper.toString(4));
		br.close();
		
	}

	private static JSONObject calculatePLT(String website, int tries) {
		Map<String, List<Long>> latency = new HashMap<>();
		latency.put("networklatency", new ArrayList<>());
		latency.put("processlatency", new ArrayList<>());
		latency.put("totallatency", new ArrayList<>());
		for (int i = 0; i < tries; i++) {
			ChromeOptions options = new ChromeOptions();
			String uuid = UUID.randomUUID().toString();
			options.addArguments("--ignore-certificate-errors", "--user-data-dir=/tmp/" + uuid);
			WebDriver driver = new ChromeDriver(options);
			driver.get(website);
			final JavascriptExecutor js = (JavascriptExecutor) driver;
			// time of the process of navigation and page load
			Map<String, Long> obj = (Map<String, Long>) js.executeScript("return window.performance.timing");
			latency.get("networklatency").add(obj.get("responseEnd") - obj.get("fetchStart"));
			latency.get("processlatency").add(obj.get("domComplete") - obj.get("domLoading"));
			latency.get("totallatency").add(obj.get("loadEventEnd") - obj.get("navigationStart"));
			driver.close();
		}
		
		JSONObject stats = new JSONObject();
		latency.forEach((k, v) -> { 
			stats.put(k, v.stream().mapToLong(Long::longValue).sum() / v.size());
		});
		return stats;
	}

}
