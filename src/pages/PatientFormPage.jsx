import { useNavigate } from "react-router-dom";
import { useState } from "react";
import AppLayout from "../components/AppLayout";
import { normalizeLanguageCode, useLanguage } from "../i18n/LanguageContext";
import { getPatientFormOverride } from "../i18n/patientFormOverrides";
import { getPatientRegistrationText } from "../i18n/patientRegistration";

const genderOptions = ["male", "female", "other"];
const educationalQualificationOptions = [
  "noFormalEducation",
  "primaryEducation",
  "secondaryEducation",
  "higherSecondary",
  "graduateAndAbove",
];
const occupationOptions = ["unemployed", "homemaker", "employed", "retired"];
const yesNoNotSureOptions = ["yes", "no", "notSure"];
const yesNoOptions = ["yes", "no"];
const dietOptions = ["vegetarian", "mixed"];
const appetiteOptions = ["normal", "lowAppetite"];
const proteinOptions = ["enoughProtein", "notEnoughProtein", "unsureProtein"];
const exerciseTypeOptions = ["walking", "stretching", "strength", "noneExercise"];
const exerciseFrequencyOptions = ["daily", "sometimes", "never"];
const languageOptions = ["en", "kn", "hi", "mr"];
const symptomOptions = [
  "weakness",
  "muscleLoss",
  "dizziness",
  "lowEnergy",
  "swelling",
  "poorSleep",
  "appetiteLoss",
];
const habitOptions = ["alcohol", "smoking", "tobacco_chewing", "none"];
const ageGroupOptions = ["age_18_30", "age_31_45", "age_46_60", "age_61_plus"];
const maritalStatusOptions = ["married", "unmarried", "widowed", "divorced_separated"];
const familyTypeOptions = ["nuclear", "joint", "extended"];
const residenceOptions = ["rural", "urban"];
const religionOptions = ["hindu", "muslim", "christian", "religion_other"];
const socioeconomicOptions = ["socioeconomic_lower", "socioeconomic_middle", "socioeconomic_upper"];
const cldDurationOptions = ["less_than_1_year", "one_to_five_years", "six_to_ten_years", "more_than_10_years"];
const cldEtiologyOptions = ["alcohol_related", "viral_hepatitis", "fatty_liver", "etiology_other"];
const cldStageOptions = ["compensated_cirrhosis", "decompensated_cirrhosis", "stage_other", "not_documented"];
const comorbidityOptions = ["diabetes", "hypertension", "comorbidity_other", "no_known_comorbidities"];
const sarcopeniaDurationOptions = ["less_than_6_months", "six_to_twelve_months", "more_than_1_year", "not_documented"];
const cldTreatmentOptions = ["medical_management_only", "medical_nutrition", "treatment_other", "complications_management"];
const hospitalizationOptions = ["never", "once", "twice", "three_or_more"];
const counsellingOptions = ["yes", "no", "not_sure"];
const previousEducationOptions = ["education_none", "education_cld", "education_sarcopenia", "education_both"];

function SectionCard({ title, helpText, children }) {
  return (
    <section className="question-card">
      <div className="mb-5 border-b border-hospital-200 pb-4">
        <h2 className="text-xl font-semibold text-hospital-900">{title}</h2>
        {helpText ? <p className="mt-1 text-sm text-hospital-700">{helpText}</p> : null}
      </div>
      <div className="grid gap-5">{children}</div>
    </section>
  );
}

function FieldPanel({ children, wide = false }) {
  return <div className={`form-panel ${wide ? "form-panel-wide" : ""}`}>{children}</div>;
}

function SingleChoice({ name, label, options, value, onChange, text, columns = "choice-grid-three" }) {
  return (
    <fieldset className="field">
      <span>{label}</span>
      <div className={`choice-grid ${columns}`}>
        {options.map((item) => (
          <label key={item} className="choice-item">
            <input type="radio" name={name} value={item} checked={value === item} onChange={onChange} />
            <span>{text(`options.${item}`)}</span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}

function MultiChoice({ name, label, options, values = [], onChange, text, columns = "choice-grid-three" }) {
  return (
    <fieldset className="field">
      <span>{label}</span>
      <div className={`choice-grid ${columns}`}>
        {options.map((item) => (
          <label key={item} className="choice-item">
            <input
              type="checkbox"
              checked={values.includes(item)}
              onChange={(event) => onChange(name, item, event.target.checked)}
            />
            <span>{text(`options.${item}`)}</span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}

export default function PatientFormPage({ patient, setPatient, onSessionStart, onExitFlow }) {
  const navigate = useNavigate();
  const [errors, setErrors] = useState({});
  const [submitError, setSubmitError] = useState("");
  const { t, setLanguage, language } = useLanguage();

  function pf(path) {
    return getPatientFormOverride(language, path) ?? t(path);
  }

  function reg(path) {
    return getPatientRegistrationText(language, path);
  }

  function handleChange(event) {
    const { name, value } = event.target;

    if (name === "languagePreference") {
      setLanguage(value);
    }

    setPatient((prev) => ({ ...prev, [name]: value }));
  }

  function handleCheckboxGroupChange(name, value, checked) {
    setPatient((prev) => {
      const rawItems = Array.isArray(prev[name]) ? prev[name] : [];
      const currentItems = name === "habits"
        ? rawItems.map((item) => item === "tobacco" ? "tobacco_chewing" : item)
        : rawItems;
      const isExclusiveNone = value === "none" || value === "no_known_comorbidities";
      const exclusiveValue = name === "habits" ? "none" : "no_known_comorbidities";
      const nextItems = checked
        ? isExclusiveNone
          ? [value]
          : [...currentItems.filter((item) => item !== exclusiveValue), value]
        : currentItems.filter((item) => item !== value);

      return { ...prev, [name]: nextItems };
    });
  }

  function validate() {
    const nextErrors = {};

    if (!patient.patientId) nextErrors.patientId = pf("patientForm.errors.patientId");
    if (!patient.ageGroup && !patient.age) nextErrors.ageGroup = reg("ageRequired");
    if (!patient.gender) nextErrors.gender = pf("patientForm.errors.gender");
    if (!patient.educationalQualification) {
      nextErrors.educationalQualification = pf("patientForm.errors.educationalQualification");
    }
    if (!patient.occupation) {
      nextErrors.occupation = pf("patientForm.errors.occupation");
    }
    if (!patient.cldStatus) nextErrors.cldStatus = pf("patientForm.errors.cldStatus");
    if (!patient.weaknessFatigue) {
      nextErrors.weaknessFatigue = pf("patientForm.errors.weaknessFatigue");
    }
    if (!patient.recentWeightLoss) {
      nextErrors.recentWeightLoss = pf("patientForm.errors.recentWeightLoss");
    }
    if (!patient.dietType) nextErrors.dietType = pf("patientForm.errors.dietType");
    if (!patient.appetiteLevel) nextErrors.appetiteLevel = pf("patientForm.errors.appetiteLevel");
    if (!patient.proteinAwareness) {
      nextErrors.proteinAwareness = pf("patientForm.errors.proteinAwareness");
    }
    if (!patient.exerciseRegular) {
      nextErrors.exerciseRegular = pf("patientForm.errors.exerciseRegular");
    }
    if (!patient.exerciseType) nextErrors.exerciseType = pf("patientForm.errors.exerciseType");
    if (!patient.exerciseFrequency) {
      nextErrors.exerciseFrequency = pf("patientForm.errors.exerciseFrequency");
    }
    if (!patient.languagePreference) {
      nextErrors.languagePreference = pf("patientForm.errors.languagePreference");
    }

    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitError("");
    if (!validate()) return;

    if (onSessionStart) {
      const result = await onSessionStart(patient);
      if (!result?.success) {
        setSubmitError(result?.error || reg("sessionStartFailed"));
        return;
      }
    }

    navigate("/pre-test");
  }

  return (
    <AppLayout
      title={pf("patientForm.title")}
      subtitle={pf("patientForm.subtitle")}
      backTo="/welcome"
      onExitFlow={onExitFlow}
    >
      <form onSubmit={handleSubmit} className="stack">
        <SectionCard
      title={reg("socioTitle")}
      helpText={reg("socioHelp")}
        >
          <div className="form-section-grid">
            <FieldPanel>
              <label className="field">
                <span>{pf("patientForm.patientId")}</span>
                <input
                  type="text"
                  name="patientId"
                  value={patient.patientId}
                  onChange={handleChange}
                  placeholder={pf("patientForm.patientIdPlaceholder")}
                  required
                />
                {errors.patientId ? <small className="error-text">{errors.patientId}</small> : null}
              </label>
            </FieldPanel>

            <FieldPanel wide>
              <SingleChoice name="ageGroup" label={reg("ageGroup")} options={ageGroupOptions} value={patient.ageGroup} onChange={handleChange} text={reg} columns="choice-grid-four" />
              {errors.ageGroup ? <small className="error-text">{errors.ageGroup}</small> : null}
            </FieldPanel>

            <FieldPanel wide>
              <fieldset className="field">
                <span>{pf("patientForm.gender")}</span>
                <div className="choice-grid choice-grid-three">
                  {genderOptions.map((item) => (
                    <label key={item} className="choice-item">
                      <input
                        type="radio"
                        name="gender"
                        value={item}
                        checked={patient.gender === item}
                        onChange={handleChange}
                      />
                      <span>{pf(`patientForm.options.${item}`)}</span>
                    </label>
                  ))}
                </div>
                {errors.gender ? <small className="error-text">{errors.gender}</small> : null}
              </fieldset>
            </FieldPanel>

            <FieldPanel wide>
              <SingleChoice name="maritalStatus" label={reg("maritalStatus")} options={maritalStatusOptions} value={patient.maritalStatus} onChange={handleChange} text={reg} columns="choice-grid-four" />
            </FieldPanel>
            <FieldPanel>
              <SingleChoice name="familyType" label={reg("familyType")} options={familyTypeOptions} value={patient.familyType} onChange={handleChange} text={reg} />
            </FieldPanel>
            <FieldPanel>
              <SingleChoice name="residence" label={reg("residence")} options={residenceOptions} value={patient.residence} onChange={handleChange} text={reg} columns="choice-grid-two" />
            </FieldPanel>
            <FieldPanel wide>
              <SingleChoice name="religion" label={reg("religion")} options={religionOptions} value={patient.religion} onChange={handleChange} text={reg} columns="choice-grid-four" />
            </FieldPanel>
            <FieldPanel>
              <SingleChoice name="socioeconomicStatus" label={reg("socioeconomicStatus")} options={socioeconomicOptions} value={patient.socioeconomicStatus} onChange={handleChange} text={reg} />
            </FieldPanel>

            <FieldPanel wide>
              <fieldset className="field">
                <span>{reg("educationStatus")}</span>
                <div className="choice-grid choice-grid-three">
                  {educationalQualificationOptions.map((item) => (
                    <label key={item} className="choice-item">
                      <input
                        type="radio"
                        name="educationalQualification"
                        value={item}
                        checked={patient.educationalQualification === item}
                        onChange={handleChange}
                      />
                      <span>{pf(`patientForm.options.${item}`)}</span>
                    </label>
                  ))}
                </div>
                {errors.educationalQualification ? (
                  <small className="error-text">{errors.educationalQualification}</small>
                ) : null}
              </fieldset>
            </FieldPanel>

            <FieldPanel wide>
              <fieldset className="field">
                <span>{pf("patientForm.occupation")}</span>
                <div className="choice-grid choice-grid-four">
                  {occupationOptions.map((item) => (
                    <label key={item} className="choice-item">
                      <input
                        type="radio"
                        name="occupation"
                        value={item}
                        checked={patient.occupation === item}
                        onChange={handleChange}
                      />
                      <span>{pf(`patientForm.options.${item}`)}</span>
                    </label>
                  ))}
                </div>
                {errors.occupation ? (
                  <small className="error-text">{errors.occupation}</small>
                ) : null}
              </fieldset>
            </FieldPanel>
            <FieldPanel wide>
              <fieldset className="field">
                <span>{reg("dietaryPattern")}</span>
                <div className="choice-grid choice-grid-three">
                  {[...dietOptions, ...(patient.dietType === "nonVegetarian" ? ["nonVegetarian"] : [])].map((item) => (
                    <label key={item} className="choice-item">
                      <input type="radio" name="dietType" value={item} checked={patient.dietType === item} onChange={handleChange} />
                      <span>{pf(`patientForm.options.${item}`)}</span>
                    </label>
                  ))}
                </div>
                {errors.dietType ? <small className="error-text">{errors.dietType}</small> : null}
              </fieldset>
            </FieldPanel>
            <FieldPanel wide>
              <MultiChoice
                name="habits"
                label={reg("habits")}
                options={habitOptions}
                values={(patient.habits || []).map((item) => item === "tobacco" ? "tobacco_chewing" : item)}
                onChange={handleCheckboxGroupChange}
                text={(key) => ["options.none", "options.tobacco_chewing", "options.alcohol", "options.smoking"].includes(key) ? reg(key) : pf(`patientForm.${key}`)}
                columns="choice-grid-four"
              />
            </FieldPanel>
          </div>
        </SectionCard>

        <SectionCard
          title={reg("clinicalTitle")}
          helpText={reg("clinicalHelp")}
        >
          <div className="form-section-grid">
            <FieldPanel>
              <fieldset className="field">
                <span>{t("patientForm.cldStatus")}</span>
                <div className="choice-grid choice-grid-three">
                  {yesNoNotSureOptions.map((item) => (
                    <label key={item} className="choice-item">
                      <input
                        type="radio"
                        name="cldStatus"
                        value={item}
                        checked={patient.cldStatus === item}
                        onChange={handleChange}
                      />
                      <span>{pf(`patientForm.options.${item}`)}</span>
                    </label>
                  ))}
                </div>
                {errors.cldStatus ? <small className="error-text">{errors.cldStatus}</small> : null}
              </fieldset>
            </FieldPanel>

            <FieldPanel wide>
              <SingleChoice name="cldEtiology" label={reg("cldEtiology")} options={cldEtiologyOptions} value={patient.cldEtiology} onChange={handleChange} text={reg} />
              {patient.cldEtiology === "etiology_other" ? <label className="field mt-3"><span>{reg("etiologyOther")}</span><input name="cldEtiologyOther" value={patient.cldEtiologyOther} onChange={handleChange} /></label> : null}
            </FieldPanel>
            <FieldPanel wide>
              <SingleChoice name="cldStage" label={reg("cldStage")} options={cldStageOptions} value={patient.cldStage} onChange={handleChange} text={reg} />
              {patient.cldStage === "stage_other" ? <label className="field mt-3"><span>{reg("stageOther")}</span><input name="cldStageOther" value={patient.cldStageOther} onChange={handleChange} /></label> : null}
            </FieldPanel>
            <FieldPanel wide>
              <MultiChoice name="comorbidities" label={reg("comorbidities")} options={comorbidityOptions} values={patient.comorbidities} onChange={handleCheckboxGroupChange} text={reg} />
              {patient.comorbidities.includes("comorbidity_other") ? <label className="field mt-3"><span>{reg("comorbiditiesOther")}</span><input name="comorbiditiesOther" value={patient.comorbiditiesOther} onChange={handleChange} /></label> : null}
            </FieldPanel>
            <FieldPanel>
              <SingleChoice name="sarcopeniaDuration" label={reg("sarcopeniaDuration")} options={sarcopeniaDurationOptions} value={patient.sarcopeniaDuration} onChange={handleChange} text={reg} />
            </FieldPanel>
            <FieldPanel wide>
              <SingleChoice name="cldTreatment" label={reg("cldTreatment")} options={cldTreatmentOptions} value={patient.cldTreatment} onChange={handleChange} text={reg} />
              {patient.cldTreatment === "treatment_other" ? <label className="field mt-3"><span>{reg("treatmentOther")}</span><input name="cldTreatmentOther" value={patient.cldTreatmentOther} onChange={handleChange} /></label> : null}
            </FieldPanel>
            <FieldPanel>
              <SingleChoice name="hospitalizationHistory" label={reg("hospitalizationHistory")} options={hospitalizationOptions} value={patient.hospitalizationHistory} onChange={handleChange} text={reg} />
            </FieldPanel>
            <FieldPanel>
              <SingleChoice name="nutritionalCounselling" label={reg("nutritionalCounselling")} options={counsellingOptions} value={patient.nutritionalCounselling} onChange={handleChange} text={reg} />
            </FieldPanel>
            <FieldPanel wide>
              <SingleChoice name="previousHealthEducation" label={reg("previousEducation")} options={previousEducationOptions} value={patient.previousHealthEducation} onChange={handleChange} text={reg} />
            </FieldPanel>

            <FieldPanel wide>
              <SingleChoice name="cldDuration" label={reg("cldDuration")} options={cldDurationOptions} value={patient.cldDuration} onChange={handleChange} text={reg} />
            </FieldPanel>

            <FieldPanel>
              <fieldset className="field">
                <span>{pf("patientForm.weaknessFatigue")}</span>
                <div className="choice-grid choice-grid-two">
                  {yesNoOptions.map((item) => (
                    <label key={item} className="choice-item">
                      <input
                        type="radio"
                        name="weaknessFatigue"
                        value={item}
                        checked={patient.weaknessFatigue === item}
                        onChange={handleChange}
                      />
                      <span>{pf(`patientForm.options.${item}`)}</span>
                    </label>
                  ))}
                </div>
                {errors.weaknessFatigue ? (
                  <small className="error-text">{errors.weaknessFatigue}</small>
                ) : null}
              </fieldset>
            </FieldPanel>

            <FieldPanel>
              <fieldset className="field">
                <span>{pf("patientForm.recentWeightLoss")}</span>
                <div className="choice-grid choice-grid-two">
                  {yesNoOptions.map((item) => (
                    <label key={item} className="choice-item">
                      <input
                        type="radio"
                        name="recentWeightLoss"
                        value={item}
                        checked={patient.recentWeightLoss === item}
                        onChange={handleChange}
                      />
                      <span>{pf(`patientForm.options.${item}`)}</span>
                    </label>
                  ))}
                </div>
                {errors.recentWeightLoss ? (
                  <small className="error-text">{errors.recentWeightLoss}</small>
                ) : null}
              </fieldset>
            </FieldPanel>
          </div>
        </SectionCard>

        <SectionCard title={pf("patientForm.dietTitle")} helpText={pf("patientForm.dietHelp")}>
          <div className="form-section-grid">
            <FieldPanel>
              <fieldset className="field">
                <span>{pf("patientForm.appetiteLevel")}</span>
                <div className="choice-grid choice-grid-two">
                  {appetiteOptions.map((item) => (
                    <label key={item} className="choice-item">
                      <input
                        type="radio"
                        name="appetiteLevel"
                        value={item}
                        checked={patient.appetiteLevel === item}
                        onChange={handleChange}
                      />
                      <span>{pf(`patientForm.options.${item}`)}</span>
                    </label>
                  ))}
                </div>
                {errors.appetiteLevel ? (
                  <small className="error-text">{errors.appetiteLevel}</small>
                ) : null}
              </fieldset>
            </FieldPanel>

            <FieldPanel wide>
              <fieldset className="field">
                <span>{pf("patientForm.proteinAwareness")}</span>
                <div className="choice-grid choice-grid-three">
                  {proteinOptions.map((item) => (
                    <label key={item} className="choice-item">
                      <input
                        type="radio"
                        name="proteinAwareness"
                        value={item}
                        checked={patient.proteinAwareness === item}
                        onChange={handleChange}
                      />
                      <span>{pf(`patientForm.options.${item}`)}</span>
                    </label>
                  ))}
                </div>
                {errors.proteinAwareness ? (
                  <small className="error-text">{errors.proteinAwareness}</small>
                ) : null}
              </fieldset>
            </FieldPanel>
          </div>
        </SectionCard>

        <SectionCard
          title={pf("patientForm.exerciseTitle")}
          helpText={pf("patientForm.exerciseHelp")}
        >
          <div className="form-section-grid-3">
            <FieldPanel>
              <fieldset className="field">
                <span>{pf("patientForm.exerciseRegular")}</span>
                <div className="choice-grid choice-grid-two">
                  {yesNoOptions.map((item) => (
                    <label key={item} className="choice-item">
                      <input
                        type="radio"
                        name="exerciseRegular"
                        value={item}
                        checked={patient.exerciseRegular === item}
                        onChange={handleChange}
                      />
                      <span>{pf(`patientForm.options.${item}`)}</span>
                    </label>
                  ))}
                </div>
                {errors.exerciseRegular ? (
                  <small className="error-text">{errors.exerciseRegular}</small>
                ) : null}
              </fieldset>
            </FieldPanel>

            <FieldPanel>
              <fieldset className="field">
                <span>{pf("patientForm.exerciseType")}</span>
                <div className="choice-grid choice-grid-two">
                  {exerciseTypeOptions.map((item) => (
                    <label key={item} className="choice-item">
                      <input
                        type="radio"
                        name="exerciseType"
                        value={item}
                        checked={patient.exerciseType === item}
                        onChange={handleChange}
                      />
                      <span>{pf(`patientForm.options.${item}`)}</span>
                    </label>
                  ))}
                </div>
                {errors.exerciseType ? (
                  <small className="error-text">{errors.exerciseType}</small>
                ) : null}
              </fieldset>
            </FieldPanel>

            <FieldPanel>
              <fieldset className="field">
                <span>{pf("patientForm.exerciseFrequency")}</span>
                <div className="choice-grid choice-grid-three">
                  {exerciseFrequencyOptions.map((item) => (
                    <label key={item} className="choice-item">
                      <input
                        type="radio"
                        name="exerciseFrequency"
                        value={item}
                        checked={patient.exerciseFrequency === item}
                        onChange={handleChange}
                      />
                      <span>{pf(`patientForm.options.${item}`)}</span>
                    </label>
                  ))}
                </div>
                {errors.exerciseFrequency ? (
                  <small className="error-text">{errors.exerciseFrequency}</small>
                ) : null}
              </fieldset>
            </FieldPanel>
          </div>
        </SectionCard>

        <SectionCard
          title={pf("patientForm.symptomsTitle")}
          helpText={pf("patientForm.symptomsHelp")}
        >
          <FieldPanel>
            <fieldset className="field">
              <span>{pf("patientForm.symptoms")}</span>
              <div className="choice-grid choice-grid-four">
                {symptomOptions.map((item) => (
                  <label key={item} className="choice-item">
                    <input
                      type="checkbox"
                      checked={patient.symptoms.includes(item)}
                      onChange={(event) =>
                        handleCheckboxGroupChange("symptoms", item, event.target.checked)
                      }
                    />
                    <span>{pf(`patientForm.options.${item}`)}</span>
                  </label>
                ))}
              </div>
            </fieldset>
          </FieldPanel>
        </SectionCard>

        <SectionCard
          title={pf("patientForm.languageTitle")}
          helpText={pf("patientForm.languageHelp")}
        >
          <FieldPanel>
            <label className="field">
              <span>{pf("patientForm.languagePreference")}</span>
              <select
                name="languagePreference"
                value={patient.languagePreference ? normalizeLanguageCode(patient.languagePreference) : ""}
                onChange={handleChange}
                required
              >
                <option value="">{pf("patientForm.selectLanguage")}</option>
                {languageOptions.map((item) => (
                  <option key={item} value={item}>
                    {t(`languages.${item}`)}
                  </option>
                ))}
              </select>
              {errors.languagePreference ? (
                <small className="error-text">{errors.languagePreference}</small>
              ) : null}
            </label>
          </FieldPanel>
        </SectionCard>

        {submitError ? <p className="error-text">{submitError}</p> : null}

        <button type="submit" className="btn btn-primary btn-block">
          {pf("patientForm.submit")}
        </button>
      </form>
    </AppLayout>
  );
}
